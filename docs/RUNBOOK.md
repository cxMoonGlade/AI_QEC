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
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_static \
  --config configs/scope_static/d3_r1_MVP05_windows.yaml
```

Full local-window sweep:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_static \
  --config configs/scope_static/d3_r1_MVP05_windows_full.yaml
```

Supported outputs include metrics JSON, graph audits, window audits,
compression accounting, model records, and heldout likelihood summaries.

## Function: Run Stage 2 Static Discovery

Direct free-assignment discovery:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_static_discovery \
  --config configs/scope_static/d3_r1_STAGE2A_full.yaml
```

Summarize Stage 2A:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.stage2a0_summary \
  --metrics outputs/scope_static/STAGE2A_full/metrics.json
```

Passive identifiability audit:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_static_identifiability \
  --config configs/scope_static/d3_r1_STAGE2A_DISC10_passive_audit.yaml
```

Robust local-inverse discovery:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_static_disc16b_robustness \
  --config configs/scope_static/d3_r1_STAGE2C_DISC16b_robustness.yaml
```

Supported outputs include evaluator-only ARI/NMI, quotient recovery metrics,
active prototype counts, collapse flags, and label-use audits.

## Function: Validate Google Set1 Predictive Utility

Native GPU path:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_google_static \
  --dataset-root /home/cx/Document/google_72Q_surface_code_d3_d5_set1 \
  --native-gpu
```

Fast smoke:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_google_static \
  --dataset-root /home/cx/Document/google_72Q_surface_code_d3_d5_set1 \
  --native-gpu \
  --train-shots 256 --heldout-shots 256 --max-windows 8 --steps 2 \
  --models hard_orbit \
  --orbit-modes fault_graph_heuristic,schedule_geometric \
  --skip-cross-sample-transfer
```

Google data has no true hidden mechanism labels. Supported claims are
predictive, calibration, transfer, and proxy-label diagnostics only.

## Function: Generate Physical-Mechanism Data

Use this function when you want noisy data from explicitly enabled mechanisms.
The maintainable interface is YAML:

```yaml
s2d_physical:
  mechanism_set: [M0, M4, M8, M24]
  mechanisms:
    M0: {p_x: 0.0015, p_y: 0.0008, p_z: 0.0022}
    M4: {gamma: 0.018}
    M8: {epsilon: 0.025}
    M24: {gamma: 0.010}
  mechanism_instance_counts:
    M0: 4
    M4: 4
    M8: 2
    M24: 2
```

The full template is
`configs/scope_static/layer1_user_defined_mechanisms.yaml`.

Small user-defined Layer 1 run:

```bash
scope-layer1-prep \
  --config configs/scope_static/layer1_user_defined_mechanisms.yaml \
  --output-dir outputs/scope_static/user_defined_layer1_demo/S2D_PHYC1_teacher
```

Physical Oracle Stack facade:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_physical_oracle_stack \
  --config configs/scope_static/d3_r1_S2D_PHYS_cudaq.yaml \
  --run-local-inverse auto
```

Layer 1 full-circuit CUDA-Q teacher:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_s2d_physical_teacher \
  --config configs/scope_static/s2d11_allM_30q_depth30.yaml \
  --output-dir outputs/scope_static/full_circuit_cudaq_allM_30q_depth30/S2D_PHYC1_teacher \
  --preflight-dir outputs/scope_static/full_circuit_cudaq_allM_30q_depth30/S2D_PHYS0_preflight
```

Layer 1 produces mechanism records, probe schedules, sampled observations,
teacher config, sampling audits, and active probe manifests.

Physicality boundary: Layer 1 mechanisms use catalog unitary/Kraus/readout
definitions. Layer 1 emits `cptp_guardrail_audit.json`, which checks unitarity,
complete-positivity representation class, declared channel dimension, Kraus
trace preservation, readout stochasticity, and parameter validity for every
enabled mechanism record.

### Full-Circuit g30 Timing Reference

The current full-circuit g30 run shows that the dominant cost is CUDA-Q
sampling inside the Layer 1 teacher. The teacher artifact records explicit
wall-clock fields; Stage 3 stage timings below use artifact end-time deltas and
should be treated as approximate upper bounds.

Instrumented Layer 1 teacher wall clock:

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

Layer 2 balanced teacher audit:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_phyc2_sampled_observation_separability \
  --contract balanced \
  --teacher-dir outputs/scope_static/full_circuit_cudaq_allM_30q_depth30/S2D_PHYC1_teacher \
  --output-dir outputs/scope_static/full_circuit_cudaq_allM_30q_depth30/PHYC2_balanced_teacher_self_distinguishment
```

Layer 2 tests teacher/catalog self-distinguishability. It is not a learner
success claim and must not emit canonical learner predictions.

## Function: Run No-Leakage Learner Recovery

Layer 3 legacy no-leakage recovery:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_phyc3_no_leakage_learner_recovery \
  --contract balanced \
  --teacher-dir outputs/scope_static/full_circuit_cudaq_allM_30q_depth30/S2D_PHYC1_teacher \
  --output-dir outputs/scope_static/full_circuit_cudaq_allM_30q_depth30/PHYC3_no_leakage_learner_recovery
```

Layer 3 quality from learner predictions:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_phyc3_sampled_quantum_error_quality \
  --teacher-dir outputs/scope_static/full_circuit_cudaq_allM_30q_depth30/S2D_PHYC1_teacher \
  --prediction-dir outputs/scope_static/full_circuit_cudaq_allM_30q_depth30/PHYC3_no_leakage_learner_recovery \
  --output-dir outputs/scope_static/full_circuit_cudaq_allM_30q_depth30/PHYC3_no_leakage_learner_quality
```

Layer 3 consumes learner-visible sampled observations. Forbidden learner inputs
include mechanism IDs, family labels, teacher self embeddings, exact channel
matrices, exact PTMs, oracle prototypes, and hidden parameters.

Layer 3 generated-noise language must distinguish two cases: catalog-mechanism
replay inherits the catalog mechanism definition, while empirical visible replay
is a visible-distribution model and is not by itself a learned CPTP channel.

## Function: Run Canonical Layer 3 Acceptance

```bash
conda run -n aiqec scope-layer3-canonical \
  --config configs/scope_static/layer3_canonical_acceptance.yaml
```

Equivalent module form:

```bash
conda run -n aiqec python -m scope_static.experiments.run_layer3_canonical_acceptance \
  --config configs/scope_static/layer3_canonical_acceptance.yaml
```

The canonical resolver selects `phyc3c_distributional_gaussian_likelihood_head`
only after Layer 2, Layer 3b, Layer 3c, and validation gates pass. It rejects
Layer 2 teacher-self predictions, legacy Layer 2 grouped predictions, and the
Layer 3a old visible-surface baseline as canonical learner evidence.

## Function: Run Stage 3A Protocol Freeze

```bash
conda run -n aiqec scope-stage3a-freeze \
  --config configs/scope_static/stage3a_protocol_freeze.yaml
```

Equivalent module form:

```bash
conda run -n aiqec python -m scope_static.experiments.run_stage3a_protocol_freeze \
  --config configs/scope_static/stage3a_protocol_freeze.yaml
```

Stage 3A writes `visible_feature_schema.json`, `forbidden_feature_audit.json`,
`split_manifest.json`, `probe_schedule_manifest.json`, `batch_context_schema.json`,
and `assignment_unit.json`. It does not train a discovery model and does not
compute the Stage 3A.5 observability ceiling.

## Function: Run Stage 3A.5 Observability Ceiling

```bash
conda run -n aiqec scope-stage3a5-ceiling \
  --config configs/scope_static/stage3a5_observability_ceiling.yaml
```

Equivalent module form:

```bash
conda run -n aiqec python -m scope_static.experiments.run_stage3a5_observability_ceiling \
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
conda run -n aiqec python -m scope_static.experiments.run_stage3b0_baselines \
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
conda run -n aiqec python -m scope_static.experiments.run_stage3b1_discovery_model \
  --config configs/scope_static/stage3b1_discovery_model.yaml
```

Stage 3B.1 consumes Stage 3A and Stage 3A.5, trains a visible-only
prototype-mixture discovery model with learned diagonal covariance, selects the
declared K mode using validation visible NLL plus a visible-only complexity
penalty over a declared capped set of Stage 3A validation folds, uses the
declared first-run iteration budget from config, and writes
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
conda run -n aiqec python -m scope_static.experiments.run_stage3c_generator_learning \
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

## Function: Run Active Physical-Observability Audits

Local Pauli-Lindblad observability:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_s2d9_local_pauli_lindblad_observability \
  --config configs/scope_static/s2d9_local_pauli_lindblad_observability.yaml
```

Generator invariant calibration:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_s2d10b_generator_invariant_calibration \
  --config configs/scope_static/s2d10b_generator_invariant_calibration.yaml
```

Typed gate/readout/prep invariant learner:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_s2d11_typed_spam_gate_invariant_learner \
  --config configs/scope_static/s2d11_typed_spam_gate_invariant_learner.yaml
```

Calibration-only audit:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_s2d11b_m1_gate_branch_grouped_calibration_audit \
  --config configs/scope_static/s2d11b_m1_gate_branch_grouped_calibration_audit.yaml
```

These functions support probe-design and observability analysis. They are not a
replacement for canonical Layer 3 acceptance.

## Output Discipline

Promote artifact files, not terminal output. Serious runs should write metrics
JSON, compact summaries, config manifests, leakage or label-use audits, and
the relevant graph/window/probe/prototype audits.

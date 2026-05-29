# Runbook

This runbook lists supported functions and reproducible commands. Use
`CONTEXT.md` for terminology and `docs/ARCHITECTURE.md` for system structure.

## Environment

Install from the repo root:

```bash
conda run -n aiqec python -m pip install -e .
```

Do not use `PYTHONPATH="$PWD/src"` for normal runs. The editable install is the
supported path.

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

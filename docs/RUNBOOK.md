# Runbook

Use this page for reproducible commands. Use `CONTEXT.md` and
`docs/ARCHITECTURE.md` for terminology and code structure.

## Environment

Install the package editable from the repo root:

```bash
conda run -n aiqec python -m pip install -e .
```

Do not set `PYTHONPATH="$PWD/src"` for normal WSL/CUDA runs. The editable
install is the supported path. `pyproject.toml` gives pytest a local source path
for tests, but experiment commands should run as installed modules.

Check CUDA visibility before serious training, Google, likelihood, or S2D runs:

```bash
conda run -n aiqec python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)"
```

If CUDA is unexpectedly unavailable, diagnose the environment. Do not treat that
as evidence for CPU-first experiment design.

CUDA-Q target smoke test for sandbox-compatible GPU access:

```bash
conda run -n aiqec python -c "import cudaq; print('cudaq', cudaq.__version__); targets=['nvidia','tensornet','tensornet-mps'];
for target in targets:
    try:
        cudaq.set_target(target)
        k = cudaq.make_kernel(); q = k.qalloc(2); k.h(q[0]); k.cx(q[0], q[1]); k.mz(q)
        print('TARGET_OK', target, cudaq.sample(k, shots_count=64))
    except Exception as exc:
        print('TARGET_ERROR', target, type(exc).__name__, str(exc))"
```

When running through the Codex sandbox, prefer CUDA-Q `make_kernel()` dynamic
kernels for smoke tests and teacher prototypes. Source-decorated
`@cudaq.kernel` GPU samples can hit a sandbox-specific CUDA driver/runtime error
even when the same target works outside the sandbox.

## Tests

Full unit test suite:

```bash
conda run -n aiqec python -m pytest -q
```

Focused S2D physical-oracle and typed-learner tests:

```bash
conda run -n aiqec python -m pytest -q \
  tests/test_physical_channels.py \
  tests/test_physical_oracle_stack.py \
  tests/test_s2d9_local_pauli_lindblad.py \
  tests/test_s2d10_generator_space_calibration.py \
  tests/test_s2d10b_generator_invariant_calibration.py \
  tests/test_s2d11_typed_spam_gate_invariant.py \
  tests/test_s2d11b_m1_gate_calibration.py
```

## Stage 1 DEM Runs

MVP05 smoke:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_static \
  --config configs/scope_static/d3_r1_MVP05_windows.yaml
```

MVP05 full local-window sweep:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_static \
  --config configs/scope_static/d3_r1_MVP05_windows_full.yaml
```

Outputs go under `outputs/scope_static/`.

## Google Set1

Native GPU Stage 1/Stage 2B validation path:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_google_static \
  --dataset-root /home/cx/Document/google_72Q_surface_code_d3_d5_set1 \
  --native-gpu
```

Fast real-data smoke:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_google_static \
  --dataset-root /home/cx/Document/google_72Q_surface_code_d3_d5_set1 \
  --native-gpu \
  --train-shots 256 --heldout-shots 256 --max-windows 8 --steps 2 \
  --models hard_orbit \
  --orbit-modes fault_graph_heuristic,schedule_geometric \
  --skip-cross-sample-transfer
```

Google local-inverse smoke:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_google_local_mechanism \
  --dataset-root /home/cx/Document/google_72Q_surface_code_d3_d5_set1 \
  --native-gpu \
  --sample-id sample_00 \
  --patch-id d3_at_q5_5 \
  --basis X \
  --rounds-label r13 \
  --dem-source decoder_si1000 \
  --orbit-mode fault_graph_heuristic \
  --train-shots 4096 \
  --heldout-shots 1024 \
  --steps 40 \
  --subsample-count 2 \
  --subsample-shots 2048 \
  --subsample-steps 30 \
  --max-windows 96 \
  --detector-pair-window-budget 48 \
  --logical-detector-pair-window-budget 48 \
  --window-plan-mode logical_aware \
  --output-root outputs/google_static
```

Google GDISC15b small grid:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_google_gdisc15b_grid \
  --dataset-root /home/cx/Document/google_72Q_surface_code_d3_d5_set1 \
  --native-gpu \
  --samples sample_00,sample_01 \
  --patches d3_at_q5_5 \
  --bases X,Z \
  --rounds-labels r13 \
  --heldout-split-types shot-heldout \
  --train-shots 4096 \
  --heldout-shots 1024 \
  --steps 40 \
  --subsample-count 2 \
  --subsample-shots 2048 \
  --subsample-steps 30 \
  --max-windows 96 \
  --detector-pair-window-budget 48 \
  --logical-detector-pair-window-budget 48 \
  --window-plan-mode logical_aware \
  --pca-ranks 1,2,3,5,8 \
  --random-control-ranks 1,2,3,5,8 \
  --random-control-seeds 0 \
  --output-dir outputs/google_static/GDISC15b_google_grid_validation
```

Google outputs go under `outputs/google_static/`.

## Stage 2 Static Discovery

Stage 2A.0 direct free-assignment discovery:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_static_discovery \
  --config configs/scope_static/d3_r1_STAGE2A_full.yaml
```

Summarize Stage 2A.0:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.stage2a0_summary \
  --metrics outputs/scope_static/STAGE2A_full/metrics.json
```

DISC10 passive identifiability audit:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_static_identifiability \
  --config configs/scope_static/d3_r1_STAGE2A_DISC10_passive_audit.yaml
```

Stage 2A.1 hardening:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_static_hardening \
  --config configs/scope_static/d3_r1_STAGE2A1_hardening.yaml
```

Stage 2C local-inverse robustness:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_static_disc16b_robustness \
  --config configs/scope_static/d3_r1_STAGE2C_DISC16b_robustness.yaml
```

## S2D Physical Oracle

Qiskit/Aer GPU preflight:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_s2d_preflight \
  --config configs/scope_static/d3_r1_S2D_PHYS_aer_gpu.yaml
```

Physical Oracle Stack facade:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_physical_oracle_stack \
  --config configs/scope_static/d3_r1_S2D_PHYS_aer_gpu.yaml \
  --run-local-inverse auto
```

The stack writes `physical_oracle_stack.json`, `physical_oracle_stack.md`, and
canonical PHYS1/PHYS2/PHYS3 stage folders under its output directory.

Local-observable GPU PHYS1 teacher for the 30-qubit depth-30 allM stress run:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_local_observable_gpu_teacher \
  --config configs/scope_static/s2d11_allM_30q_depth30.yaml \
  --output-dir outputs/scope_static/local_observable_gpu_allM_30q_depth30_30groups_v2_slot_remap/S2D_PHYS1_teacher
```

PHYC2-balanced sampled-observation mechanism-separability audit:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_phyc2_sampled_observation_separability \
  --contract balanced \
  --teacher-dir outputs/scope_static/local_observable_gpu_allM_30q_depth30_30groups_v2_slot_remap/S2D_PHYS1_teacher \
  --output-dir outputs/scope_static/local_observable_gpu_allM_30q_depth30_30groups_v2_slot_remap/PHYC2_balanced_slot_only_control

conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_phyc3_sampled_quantum_error_quality \
  --teacher-dir outputs/scope_static/local_observable_gpu_allM_30q_depth30_30groups_v2_slot_remap/S2D_PHYS1_teacher \
  --phyc2-dir outputs/scope_static/local_observable_gpu_allM_30q_depth30_30groups_v2_slot_remap/PHYC2_balanced_slot_only_control \
  --output-dir outputs/scope_static/local_observable_gpu_allM_30q_depth30_30groups_v2_slot_remap/PHYC3_quantum_error_quality
```

Current evidence for `configs/scope_static/s2d11_allM_30q_depth30.yaml`
(`local_observable_response_model: separability_v2`,
`balanced_min_instances_per_mechanism: 30`):

```text
PHYC2-balanced allM, 30 qubits, depth 30, 30 groups, 10k shots:
  contract_passed: true
  balanced_accuracy: 1.0000
  min_class_recall: 1.0000
  real_minus_within_branch_scrambled_balanced_accuracy: 0.8567
  PHYC3_quantum_error_quality_contract_passed: true
  PHYC3_mean_predicted_channel_distance: 0.000085
  PHYC3_max_predicted_channel_distance: 0.003292
```

The local-observable teacher writes
`self_distinguishability_preflight.json` and records
`sampling.observation_slot_remap`. The slot remap is expected for this teacher:
it assigns non-overlapping per-mechanism observation slots inside each circuit
batch so local responses do not overwrite each other in `observations.npz`.
PHYC2 neutralizes the synthetic slot-geometry columns for slot-remapped records;
branch flags, probe metadata, sampled response moments, and pair correlations
remain learner-visible.
Each PHYC2 report includes `slot_only_leakage_control`, which trains the same
grouped classifier using only observation slots, original physical qubits, probe
block ids, and slot/layout metadata. It must stay low; high slot-only accuracy
means the remap/layout metadata are leaking mechanism identity.

PHYC3 sampled quantum-error quality consumes the PHYC2 grouped predictions and
asks whether the predicted mechanism labels translate into close fold-trained
quantum/readout error prototypes. For `separability_v2`, this is a
mechanism-to-error translation diagnostic; it is not proof that the sampled
observations themselves were generated by Born-rule circuit physics.

PHYC2-weighted sampled-observation audit for uneven schedule-like support:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_local_observable_gpu_teacher \
  --config configs/scope_static/s2d11_allM_30q_depth30_weighted.yaml \
  --output-dir outputs/scope_static/local_observable_gpu_allM_30q_depth30_weighted_v2_slot_remap/S2D_PHYS1_teacher

conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_phyc2_sampled_observation_separability \
  --contract weighted \
  --teacher-dir outputs/scope_static/local_observable_gpu_allM_30q_depth30_weighted_v2_slot_remap/S2D_PHYS1_teacher \
  --output-dir outputs/scope_static/local_observable_gpu_allM_30q_depth30_weighted_v2_slot_remap/PHYC2_weighted_slot_only_control

conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_phyc3_sampled_quantum_error_quality \
  --teacher-dir outputs/scope_static/local_observable_gpu_allM_30q_depth30_weighted_v2_slot_remap/S2D_PHYS1_teacher \
  --phyc2-dir outputs/scope_static/local_observable_gpu_allM_30q_depth30_weighted_v2_slot_remap/PHYC2_weighted_slot_only_control \
  --output-dir outputs/scope_static/local_observable_gpu_allM_30q_depth30_weighted_v2_slot_remap/PHYC3_quantum_error_quality
```

Current evidence for
`configs/scope_static/s2d11_allM_30q_depth30_weighted.yaml`:

```text
PHYC2-weighted allM, 30 qubits, depth 30, uneven support 2-8, 10k shots:
  contract_passed: true
  balanced_accuracy: 1.0000
  min_class_recall: 1.0000
  prevalence_weighted_accuracy: 1.0000
  rare_class_recall_min: 1.0000
  real_minus_within_branch_scrambled_balanced_accuracy: 0.8779
  slot_only_leakage_control_balanced_accuracy: 0.0313
  slot_only_leakage_suspected: false
  PHYC3_quantum_error_quality_contract_passed: true
  PHYC3_mean_predicted_channel_distance: 0.000026
  PHYC3_max_predicted_channel_distance: 0.001364
  PHYC3_incompatible_predictions: 0
```

No-remap weighted ablation:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_local_observable_gpu_teacher \
  --config configs/scope_static/s2d11_allM_30q_depth30_weighted.yaml \
  --disable-slot-remap \
  --output-dir outputs/scope_static/local_observable_gpu_allM_30q_depth30_weighted_v2_no_slot_remap/S2D_PHYS1_teacher

conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_phyc2_sampled_observation_separability \
  --contract weighted \
  --teacher-dir outputs/scope_static/local_observable_gpu_allM_30q_depth30_weighted_v2_no_slot_remap/S2D_PHYS1_teacher \
  --output-dir outputs/scope_static/local_observable_gpu_allM_30q_depth30_weighted_v2_no_slot_remap/PHYC2_weighted_no_slot_remap_ablation
```

Expected diagnostic relation:

```text
PHYC2.no_slot_remap_ablation weighted BA: 0.9708
PHYC2.weighted slot-remap weighted BA:     1.0000
```

74-qubit depth-200 weighted allM scalability smoke:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_local_observable_gpu_teacher \
  --config configs/scope_static/s2d11_allM_74q_depth200_weighted.yaml \
  --output-dir outputs/scope_static/local_observable_gpu_allM_74q_depth200_weighted_v2_slot_remap/S2D_PHYS1_teacher

conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_phyc2_sampled_observation_separability \
  --contract weighted \
  --teacher-dir outputs/scope_static/local_observable_gpu_allM_74q_depth200_weighted_v2_slot_remap/S2D_PHYS1_teacher \
  --output-dir outputs/scope_static/local_observable_gpu_allM_74q_depth200_weighted_v2_slot_remap/PHYC2_weighted_slot_only_control

conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_phyc3_sampled_quantum_error_quality \
  --teacher-dir outputs/scope_static/local_observable_gpu_allM_74q_depth200_weighted_v2_slot_remap/S2D_PHYS1_teacher \
  --phyc2-dir outputs/scope_static/local_observable_gpu_allM_74q_depth200_weighted_v2_slot_remap/PHYC2_weighted_slot_only_control \
  --output-dir outputs/scope_static/local_observable_gpu_allM_74q_depth200_weighted_v2_slot_remap/PHYC3_quantum_error_quality
```

Current evidence:

```text
PHYC2-weighted allM, 74 qubits, depth 200, uneven support 2-8, 10k shots:
  contract_passed: true
  balanced_accuracy: 1.0000
  min_class_recall: 1.0000
  prevalence_weighted_accuracy: 1.0000
  rare_class_recall_min: 1.0000
  slot_only_leakage_control_balanced_accuracy: 0.0479
  slot_only_leakage_suspected: false
  teacher_total_requested_bits: 1,704,960,000
  teacher_total_seconds: 4.0741
  artifact_size: 1.7G
  PHYC3_quantum_error_quality_contract_passed: true
  PHYC3_mean_predicted_channel_distance: 0.000026
  PHYC3_max_predicted_channel_distance: 0.001364
```

For weighted local-observable teachers, add `mechanism_instance_counts` to the
S2D physical config. Unspecified enabled mechanisms use
`balanced_min_instances_per_mechanism`; explicit `0` omits a mechanism from the
teacher artifact.

## S2D Active Observability And Typed Learners

S2D.9 local Pauli-Lindblad observability:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_s2d9_local_pauli_lindblad_observability \
  --config configs/scope_static/s2d9_local_pauli_lindblad_observability.yaml
```

S2D.10b generator invariant calibration:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_s2d10b_generator_invariant_calibration \
  --config configs/scope_static/s2d10b_generator_invariant_calibration.yaml
```

S2D.11 typed gate/readout/prep invariant learner:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_s2d11_typed_spam_gate_invariant_learner \
  --config configs/scope_static/s2d11_typed_spam_gate_invariant_learner.yaml
```

S2D.11b M1 gate-branch grouped calibration audit:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_s2d11b_m1_gate_branch_grouped_calibration_audit \
  --config configs/scope_static/s2d11b_m1_gate_branch_grouped_calibration_audit.yaml
```

S2D.11b consumes the existing S2D.11 artifact tree and performs no new teacher
sampling.

## Output Hygiene

Each serious run should produce:

- config or run manifest.
- metrics JSON.
- compact summary markdown.
- leakage or claim-boundary audit when hidden labels or oracle features exist.
- graph/window/compression audits for DEM likelihood runs.
- grouped-fold and scrambled-control audits for S2D typed learner runs.

Do not promote a result by terminal output alone. The artifact tree is the
evidence object.

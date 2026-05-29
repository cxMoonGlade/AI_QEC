# Agent Notes

Use `CONTEXT.md` first for glossary and claim boundaries, then route to the
stage-specific docs:

- `docs/SCOPE_STATIC_MVP.md`: Stage 1 known-orbit DEM fault-logit MVP.
- `docs/SCOPE_STATIC_DISC.md`: Stage 2 static discovery plan.
- `docs/ARCHITECTURE.md`: current code architecture and module map.
- `docs/RUNBOOK.md`: install, test, GPU, and experiment commands.
- `docs/STAGE2_ROADMAP.md`: compact Stage 2 execution state.
- `docs/error_mechanisms.md`: physical-error mechanism taxonomy and adoption map.
- `docs/SCOPE_TWIN.md`: full SCOPE-Twin notation and future object contract.
- `docs/adr/`: durable architecture and milestone-gating decisions.

## Current Scope

The implemented package is `scope_static`. It is a fixed-context DEM/Bernoulli
research stack, not a CPTP/GKSL physical-channel learner.

The project-level problem is the six-axis physical generation problem: prove
that a physically constrained generation model holds simultaneously in
generation fidelity, interpretability, decoder utility, cross-context
generalization, drift prediction, and identifiability. CPTP/GKSL structure is a
constraint mechanism, not the full claim by itself.

Stage 1 learns fault logits over a canonicalized detector error model:

```text
e_j ~ Bernoulli(p_j)
y = A e mod 2
```

Keep notation aligned with `docs/SCOPE_TWIN.md`:

- `A` is the DEM parity map.
- `e in {0,1}^M` is the latent effective-fault vector.
- `y in {0,1}^B` is the observed detector/logical bit vector.
- `lambda_j` is the Stage 1 fault logit.
- `omega(j)` is a known orbit assignment.
- `S` or `Pi` is a learned Stage 2 discovery assignment.
- Do not use `o` for orbit or observable.
- Do not use `ell_j` for logits.

## Numerical Floor Policy

Use `scope_static.numerics.NUMERICAL_ZERO == 1e-12` for floating numerical
floors, simulation thresholds, probability floors, and leftover/complement
probabilities that would otherwise become exact `0.0`. This value is chosen to
survive square/cube operations in GPU float32. `NUMERICAL_FLOOR` exists only as
a descriptive alias. Do not replace structural zeros: Pauli/operator matrix
entries, bit values, integer indices, counts, labels, array sizes,
empty-artifact metrics, and exact algebraic identities must remain exact zeros
where required.

## GPU-First Execution

Treat this repository as a GPU-heavy QEC research program. Assume the target
workstation has a CUDA device, at least RTX 5090 class, even if the current
agent sandbox/session cannot see it. For any serious training, likelihood,
local-window, Google-data, or large ablation workflow, prefer native GPU
execution and accelerate with CUDA/PyTorch/C++ extensions as much as the code
path permits.

Before long runs, verify CUDA visibility from the `aiqec` environment. Failure
to see CUDA in one agent/session is an environment visibility problem to
diagnose, not evidence that the project should fall back to CPU-first design:

```bash
conda run -n aiqec python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)"
```

When running GPU commands through Codex, make sure the exact command prefix is
approved to run outside the sandbox. Wrappers such as `/usr/bin/time` or Conda's
`--no-capture-output` can otherwise execute inside the sandbox and make Torch
report no CUDA/NVML even though the workstation GPU is healthy. Prefer in-process
`time.perf_counter()` wall-clock reporting for benchmark metrics, or request an
approval for the wrapped command before treating CUDA invisibility as a real
runtime failure.

For S1.6 Google runs, use the native GPU path unless deliberately testing CPU
behavior:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_google_static \
  --dataset-root /home/cx/Document/google_72Q_surface_code_d3_d5_set1 \
  --native-gpu
```

If GPU utilization is low, do not assume the GPU path is broken. First check
whether the workload is launch-bound or CPU-preprocessing-bound: local exact
windows with small `max_window_bits` can finish in short CUDA bursts, while
window/cache construction, `.b8` loading, Stim/DEM parsing, and cross-sample
bookkeeping may still dominate CPU time. When improving performance, prioritize
moving repeated preprocessing and cache construction out of Python loops, reusing
prepared GPU caches across models/samples, and adding native CUDA/C++ kernels for
hot paths.

## Commands

Install:

```bash
conda run -n aiqec python -m pip install -e .
```

Test:

```bash
conda run -n aiqec python -m pytest -q
```

Run MVP05 smoke:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_static --config configs/scope_static/d3_r1_MVP05_windows.yaml
```

Run MVP05 full:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_static --config configs/scope_static/d3_r1_MVP05_windows_full.yaml
```

Run Physical Oracle Stack facade:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_physical_oracle_stack \
  --config configs/scope_static/d3_r1_S2D_PHYS_cudaq.yaml \
  --run-local-inverse auto
```

Run S2D.11 typed learner and S2D.11b calibration audit:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_s2d11_typed_spam_gate_invariant_learner \
  --config configs/scope_static/s2d11_typed_spam_gate_invariant_learner.yaml

conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_s2d11b_m1_gate_branch_grouped_calibration_audit \
  --config configs/scope_static/s2d11b_m1_gate_branch_grouped_calibration_audit.yaml
```

Run PHYC2/PHYC3 local-observable weighted allM evidence:

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

Do not use `PYTHONPATH="$PWD/src"` for normal runs on this WSL/CUDA setup. The
package should be installed editable; setting `PYTHONPATH` can interfere with
PyTorch CUDA/NVML discovery.

## Evidence Discipline

Stage 1 evidence must include seed-aware summaries, graph/window audits,
compression accounting, and baseline comparisons against `local`, `dmle_qec`,
`hard_orbit`, and `soft_feature_orbit`.

Soft residual claims require nonzero centered within-orbit feature rank.
Compression claims require explicit parameter audits.

Stage 2 discovery should begin with synthetic teachers and report ARI/NMI before
using Google repetition-code or surface-code data as external empirical
validation.

## Current PHYC2/PHYC3 Milestone Boundary

The current physical-teacher stack has three distinct roles:

```text
PHYC2-separability_v2:
  engineered separability stress teacher

PHYC2-Born-local:
  exact local Born-rule diagnostic, effective depth one

PHYC2-full-circuit-cudaq:
  required Stage 2E gate: literal n-qubit noisy circuits at gate depth d
```

The `separability_v2` allM artifacts pass PHYC2-balanced, PHYC2-weighted,
slot-only leakage control, no-remap ablation, 74q/depth200 scalability smoke,
and PHYC3 mechanism-to-error prototype quality. This is strong Stage 2
separability evidence, not a Born-rule physical baseline. The minimal Born-local
teacher remains a density-matrix diagnostic with effective circuit depth one.
Stage 2E acceptance now requires the full-circuit CUDA-Q teacher: sample literal
n-qubit noisy circuits with the configured gate depth applied in the schedule.
M11 spectator crosstalk RZ/ZZ remains a contract-sensitive mechanism; do not
collapse it into a local Born diagnostic when making full-circuit claims.

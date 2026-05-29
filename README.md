# AI QEC

Pre-release toolbox for SCOPE-style quantum-error-correction noise learning.

The project-level problem is to learn a physically constrained generation model
for QEC data whose constraint is more than the words CPTP/GKSL. The real bar is
whether the model can be validated simultaneously along six axes:

- generation fidelity.
- interpretability.
- decoder utility.
- cross-context generalization.
- drift prediction.
- identifiability.

The implemented package is `scope_static`. It exposes a toolbox of reusable
data-generation, teacher-audit, learner-recovery, and visible noise-generation
diagnostics. Its main Stage 1 object is a fixed-context DEM/Bernoulli learner:

```text
e_j ~ Bernoulli(p_j)
y = A e mod 2
```

Here `A in F_2^{B x M}` is the DEM parity map, `e in {0,1}^M` is the
latent effective-fault vector for one shot, and `y in {0,1}^B` is the observed
detector/logical bit vector. `M` is the number of effective DEM fault
mechanisms after duplicate-mask canonicalization, `B` is the number of
observation bits, and `lambda_j = logit(p_j)` is the Stage 1 fault logit.

Stage 2 also contains a layered physical-mechanism recovery stack. Historical
code and artifact names may still say `PHYC`; the public pre-release names are:

```text
Layer 1: Data Preparation (Prep)
Layer 2: Teacher Self-Distinguishment (Teacher)
Layer 3: Learner Classification and Noise Generation (Learner)
```

Layer 1 generates mechanism-catalog records, probe schedules, sampled
observations, and teacher metadata. Layer 2 verifies that the teacher/catalog
can self-distinguish its generated mechanisms. Layer 3 consumes only
learner-visible observations to classify mechanisms and generate/scored visible
noise distributions with channel-distance, NLL, and MAE diagnostics.

Stage 2 validated the physical mechanism catalog and the no-leakage visible
recovery protocol. Stage 3 now removes direct mechanism-label supervision and
tests whether SCOPE-Discovery can recover latent mechanism structure,
assignments, and prototypes from the same learner-visible observation surface.

The current physical-teacher source variants are:

```text
separability_v2:
  engineered separability stress teacher

Born-local:
  mathematically correct local diagnostic, effective depth one

full-circuit-cudaq:
  literal full n-qubit CUDA-Q teacher at configured circuit depth
```

The current canonical Layer 3 artifact accepts
`phyc3c_distributional_gaussian_likelihood_head` as the learner source, with
BA/ARI/NMI/min recall/M13 recall all equal to `1.0`, zero incompatible
predictions, mean predicted channel distance `5.64e-05`, visible Gaussian NLL
`0.226681`, and raw visible-feature MAE `4.888e-06`.

## Docs

- `CONTEXT.md`: glossary and claim boundaries.
- `docs/TOOLBOX.md`: installable toolbox commands and layer data products.
- `docs/ARCHITECTURE.md`: current package architecture and data flows.
- `docs/RUNBOOK.md`: install, test, GPU, and experiment commands.
- `docs/PRE_RELEASE_LAYERS.md`: public Layer 1/2/3 naming, data products, and current evidence.
- `docs/SCOPE_STATIC_MVP.md`: Stage 1 known-orbit DEM MVP.
- `docs/SCOPE_STATIC_DISC.md`: Stage 2 discovery and physical-oracle notes.
- `docs/STAGE2_ROADMAP.md`: compact Stage 2 execution state.
- `docs/error_mechanisms.md`: physical-error mechanism taxonomy and adoption map.
- `docs/SCOPE_TWIN.md`: future SCOPE-Twin contract.
- `AGENTS.md`: agent runbook and GPU-first execution rules.

## Setup

Use the editable install from the repo root:

```bash
conda run -n aiqec python -m pip install -e .
```

Do not set `PYTHONPATH` for normal WSL/CUDA runs; it can interfere with
PyTorch CUDA/NVML discovery.

Check GPU visibility before serious runs:

```bash
conda run -n aiqec python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)"
```

## Toolbox Commands

After editable install, the pre-release toolbox exposes:

```bash
conda run -n aiqec scope-static-toolbox
conda run -n aiqec scope-layer1-prep --help
conda run -n aiqec scope-layer2-teacher --help
conda run -n aiqec scope-layer3-canonical --help
```

The current public canonical Layer 3 acceptance run is:

```bash
conda run -n aiqec scope-layer3-canonical \
  --config configs/scope_static/layer3_canonical_acceptance.yaml
```

## Test

```bash
conda run -n aiqec python -m pytest -q
```

Focused Stage 2D slice:

```bash
conda run -n aiqec python -m pytest -q \
  tests/test_s2d9_local_pauli_lindblad.py \
  tests/test_s2d10_generator_space_calibration.py \
  tests/test_s2d10b_generator_invariant_calibration.py \
  tests/test_s2d11_typed_spam_gate_invariant.py
```

Focused Layer 2/Layer 3 local-observable slice:

```bash
conda run -n aiqec python -m pytest -q \
  tests/test_local_observable_teacher.py \
  tests/test_phyc2_sampled_observation_separability.py \
  tests/test_phyc3_sampled_quantum_error_quality.py
```

## Common Runs

Full command catalog: `docs/RUNBOOK.md`.

Stage 1 smoke:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_static \
  --config configs/scope_static/d3_r1_MVP05_windows.yaml
```

Stage 1 full local-window sweep:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_static \
  --config configs/scope_static/d3_r1_MVP05_windows_full.yaml
```

Stage 2A synthetic DEM discovery:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_static_discovery \
  --config configs/scope_static/d3_r1_STAGE2A_full.yaml
```

Stage 2D typed physical-oracle audit:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_s2d11_typed_spam_gate_invariant_learner \
  --config configs/scope_static/s2d11_typed_spam_gate_invariant_learner.yaml
```

Stage 2D S2D.11b M1 gate-branch calibration audit:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_s2d11b_m1_gate_branch_grouped_calibration_audit \
  --config configs/scope_static/s2d11b_m1_gate_branch_grouped_calibration_audit.yaml
```

Layer 2/Layer 3 local-observable weighted allM evidence:

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

Physical Oracle Stack facade:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_physical_oracle_stack \
  --config configs/scope_static/d3_r1_S2D_PHYS_cudaq.yaml \
  --run-local-inverse auto
```

Outputs are written under `outputs/scope_static/`.

## Current Stage 2 State

S2D.9 showed local two-qubit Pauli-Lindblad generator coordinates are
algebraically observable from `rzz_local_tomography`.

S2D.10b showed scalar invariants make the M8/M9/M10/M12 gate-family signal much
more usable.

S2D.11 promotes those invariants into a typed learner:

```text
measure -> readout_branch
reset   -> prep_reset_branch
other   -> gate_process_branch
```

S2D.11 set_D was close but not a strict pass:

```text
balanced accuracy: 0.8689
macro F1:          0.8614
min recall:        0.3333
readout branch:    M1/M2/M3/M16
prep/reset branch: M17-M18
main weakness:     M8 grouped-fold recall
```

S2D.11b reuses the S2D.11 artifacts, changes only gate-branch M8 calibration,
and passes the set_D acceptance checks. Some artifact names still say `M1`
because that stage predated the M0-M34 renumbering:

```text
best variant:       typed_linear_plus_M1_logit_boost
balanced accuracy:  0.8946
macro F1:           0.8927
M8 recall:          0.6667
gate recall:        1.0000
readout recall:     0.9630
prep/reset recall:  1.0000
```

The local-observable Torch CUDA allM stress teacher now passes:

```text
Layer 2 balanced 30q/depth30/30 groups: BA 1.0000, min recall 1.0000
Layer 2 weighted 30q/depth30/support 2-8: prevalence accuracy 1.0000
Layer 2 weighted 74q/depth200/support 2-8: prevalence accuracy 1.0000
Layer 3 weighted mechanism-to-error quality: mean channel distance 0.000026
slot-only leakage controls: low, leakage_suspected false
```

The canonical pre-release Layer 3 path now additionally reports visible
generation quality: Gaussian NLL, population cross entropy, and raw/population/
expectation MAE. See `docs/PRE_RELEASE_LAYERS.md`.

## Claim Boundary

Valid claims:

- fixed-context DEM/Bernoulli likelihood experiments;
- known-orbit and discovered-sharing comparisons;
- synthetic teacher ARI/NMI and heldout likelihood audits;
- local physical-oracle observability diagnostics when explicitly labeled as
  synthetic S2D experiments.

Invalid claims:

- general CPTP/GKSL learning from hardware;
- learned full noisy-circuit Born-rule likelihood from hardware data;
- real-hardware ground-truth latent mechanism recovery;
- temporal drift or context-conditioned amortization as current implemented
  evidence.

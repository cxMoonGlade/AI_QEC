# AI QEC

Research code for SCOPE-style quantum-error-correction noise learning.

The implemented package is `scope_static`. Its main production object is a
fixed-context DEM/Bernoulli learner:

```text
e_j ~ Bernoulli(p_j)
y = A e mod 2
```

Stage 2 also contains synthetic physical-oracle diagnostics for local
mechanism observability. Those diagnostics use learner-visible shot data and
local reconstructed PTM/generator summaries, but they are not a hardware
CPTP/GST learner.

## Docs

- `CONTEXT.md`: glossary and claim boundaries.
- `docs/SCOPE_STATIC_MVP.md`: Stage 1 known-orbit DEM MVP.
- `docs/SCOPE_STATIC_DISC.md`: Stage 2 discovery and physical-oracle notes.
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

## Common Runs

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

Stage 2D latest typed physical-oracle audit:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_s2d11_typed_spam_gate_invariant_learner \
  --config configs/scope_static/s2d11_typed_spam_gate_invariant_learner.yaml
```

Outputs are written under `outputs/scope_static/`.

## Current Stage 2D State

S2D.9 showed local two-qubit Pauli-Lindblad generator coordinates are
algebraically observable from `rzz_local_tomography`.

S2D.10b showed scalar invariants make the M1/M7/M8/M10 gate-family signal much
more usable.

S2D.11 promotes those invariants into a typed learner:

```text
measure -> readout_branch
reset   -> prep_reset_branch
other   -> gate_process_branch
```

Latest set_D run is close but not a strict pass:

```text
balanced accuracy: 0.8689
macro F1:          0.8614
min recall:        0.3333
M5 split count:    1
M11 preflight:     pass
main weakness:     M1 grouped-fold recall
```

## Claim Boundary

Valid claims:

- fixed-context DEM/Bernoulli likelihood experiments;
- known-orbit and discovered-sharing comparisons;
- synthetic teacher ARI/NMI and heldout likelihood audits;
- local physical-oracle observability diagnostics when explicitly labeled as
  synthetic S2D experiments.

Invalid claims:

- general CPTP/GKSL learning from hardware;
- full noisy-circuit Born-rule likelihood;
- real-hardware ground-truth latent mechanism recovery;
- temporal drift or context-conditioned amortization as current implemented
  evidence.

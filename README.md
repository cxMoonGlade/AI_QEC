# AI QEC

Research code for the SCOPE family of quantum-error-correction noise-learning
experiments.

The current implemented package is `scope_static`, a fixed-context
DEM/Bernoulli fault-logit research stack. It learns effective detector error
model fault probabilities through the parity-map likelihood:

```text
e_j ~ Bernoulli(p_j)
y = A e mod 2
A in F_2^{B x M}
```

## Documentation Map

- `CONTEXT.md`: short glossary and claim boundaries.
- `docs/SCOPE_STATIC_MVP.md`: Stage 1 SCOPE-Static known-orbit MVP.
- `docs/SCOPE_STATIC_DISC.md`: Stage 2 SCOPE-Static discovery plan.
- `docs/SCOPE_TWIN.md`: larger SCOPE-Twin object contract and notation.
- `docs/adr/0001-python-cuda-dem-mvp.md`: Python plus C++/CUDA architecture
  decision.

## Setup

From the repository root:

```bash
conda run -n aiqec python -m pip install -e .
```

Do not set `PYTHONPATH` for normal runs in the current WSL/CUDA setup. The
package is installable, and exporting `PYTHONPATH` can interfere with
PyTorch CUDA/NVML discovery on this machine.

## Tests

```bash
conda run -n aiqec python -m pytest -q
```

## Stage 1 Runs

MVP05 smoke:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_static --config configs/scope_static/d3_r1_MVP05_windows.yaml
```

MVP05 full local-window sweep:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_static --config configs/scope_static/d3_r1_MVP05_windows_full.yaml
```

Outputs are written under `outputs/scope_static/`.

## Claim Boundary

Stage 1 may claim evidence about known-orbit sharing, fixed residual features,
exact DEM likelihoods, local exact windows, compression audits, and
`d_Q^DEM` inside the fixed DEM/Bernoulli family.

It must not claim CPTP/GKSL channel learning, full noisy-circuit Born-rule
likelihood, context-conditioned amortization, temporal drift tracking, or
real-hardware ground-truth orbit recovery.

Stage 2 static discovery is currently a specification in
`docs/SCOPE_STATIC_DISC.md`; it should start with synthetic teachers where the
hidden partition is known.

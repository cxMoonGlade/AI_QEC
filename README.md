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

## Stage 2A Runs

Stage 2A is the synthetic identifiability test for DEM-fault quotient discovery:
it learns `S[j,k]` while hidden `omega(j)` is available only to the synthetic
teacher and evaluator.

Full Stage 2A run:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_static_discovery --config configs/scope_static/d3_r1_STAGE2A_full.yaml
```

This one config runs the matched-`K` exact-orbit recovery, the exact-orbit
prototype-count sweep, and the soft-residual discovery scenario.

## Stage 2B Google Validation

Google real data can compare discovery models against the S1.7 logical-aware
baselines on heldout excess NLL, calibration, transfer, and parameter/Pareto
metrics. It cannot claim true latent quotient recovery because Google data does
not provide ground-truth `omega(j)`.

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_google_static \
  --dataset-root /home/cx/Document/google_72Q_surface_code_d3_d5_set1 \
  --native-gpu \
  --models local,dmle_qec,hard_orbit,soft_feature_orbit,disc_hard,disc_soft \
  --orbit-modes fault_graph_heuristic,schedule_geometric \
  --window-plan-mode logical_aware \
  --discovery-restarts 4 \
  --discovery-prototype-counts O \
  --cross-sample-transfer \
  --output-dir outputs/google_static/S2B_discovery_logical_aware
```

## Claim Boundary

Stage 1 may claim evidence about known-orbit sharing, fixed residual features,
exact DEM likelihoods, local exact windows, compression audits, and
`d_Q^DEM` inside the fixed DEM/Bernoulli family.

It must not claim CPTP/GKSL channel learning, full noisy-circuit Born-rule
likelihood, context-conditioned amortization, temporal drift tracking, or
real-hardware ground-truth orbit recovery.

Stage 2A static discovery is implemented as a synthetic-first identifiability
path. It may claim hidden DEM-fault quotient recovery only for synthetic
teachers with evaluator-visible `omega(j)` and seed-aware ARI/NMI plus heldout
likelihood comparisons to matched known-orbit oracles. Google data remains
Stage 2B external validation and cannot support true latent quotient recovery
claims without ground-truth `omega(j)` or an explicitly defined proxy partition.

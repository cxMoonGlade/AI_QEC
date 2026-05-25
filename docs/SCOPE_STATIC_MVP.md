# SCOPE-Static DEM Fault-Logit MVP

This MVP studies SCOPE-Static at the DEM parity-map level only.

The learned object is a Bernoulli fault-logit field over a fixed canonicalized detector error model:

```text
e_j ~ Bernoulli(p_j)
y = A e mod 2
A in F_2^{B x M}
```

`B` is the number of detector plus logical observable bits. `M` is the number of effective DEM fault mechanisms after duplicate-mask canonicalization. `O` is the number of known orbits. `r` is the fixed residual feature rank. `K_t` is reserved for later SCOPE-Discovery prototype counts.

## Claim Boundary

This stage may claim evidence about orbit sharing, fixed residual features, exact DEM likelihood, and `d_Q^DEM` inside this fixed Bernoulli parity-map family.

This stage must not claim CPTP/GKSL learning, full noisy-circuit Born-rule likelihood, context-conditioned amortization, latent quotient discovery, OOD transfer, or temporal drift tracking.

## Baselines

- `local`: fully independent DEM fault logits with neutral initialization.
- `dmle_qec`: DMLE-QEC-style independent DEM prior-logit MLE baseline. It follows the compatible Stage-1 interpretation of [cxMoonGlade/DMLE-QEC](https://github.com/cxMoonGlade/DMLE-QEC): initialize independent DEM priors from the DEM, then optimize those priors by differentiable detector-syndrome NLL. In this package the detector-syndrome NLL is computed by the exact parity-map backend, and learned logits are evaluated with the common Stage-1 metrics.
- `hard_orbit`: one logit per known orbit.
- `soft_feature_orbit`: one orbit logit plus centered fixed residual features per known orbit. MVP04 selects residual feature columns by within-orbit centered energy, so the soft model is only credited when its features actually vary inside known orbits. Optional `beta_l2` regularizes the soft residual coefficients.

## Likelihood

Stim is used to construct DEMs and can be used to sample from Stim circuits. The training likelihood is not Stim sampling. The exact claim path uses the DEM parity-map likelihood:

```text
q_0(0) = 1
q_0(s != 0) = 0

q_j(s) =
    (1 - p_j) q_{j-1}(s)
    + p_j q_{j-1}(s xor a_j)
```

Repeated observations are aggregated before NLL evaluation by default.

## Sample Efficiency

`shots_to_threshold` is seed-aware. The default policy is `threshold_seed_policy: mean`, which requires the mean `Delta_NLL_oracle` across seeds at a shot budget to pass:

```text
mean_seed Delta_NLL_oracle <= threshold_epsilon
```

Use `threshold_seed_policy: all` when the threshold should require every seed at that shot budget to pass. A single lucky seed is never allowed to determine the reported threshold for a multi-seed group.

Rank-sweep runs also group thresholds by `residual_rank`; a passing rank-5 soft model cannot satisfy the threshold for rank 0, 1, or 2.

## Canonicalization

Duplicate parity masks are canonicalized before learning one effective logit per unique nonzero mask. For a duplicate raw group `G`, the effective probability is:

```text
p_eff(G) = (1 - prod_{j in G}(1 - 2 p_j)) / 2
```

Every run writes graph audit metadata including `B`, raw and effective `M`, duplicate groups, `gf2_rank(A)`, and `2^B`.

## Running

From a fresh checkout, either install the package in editable mode:

```bash
conda run -n aiqec python -m pip install -e .
```

or run commands with `PYTHONPATH=src`.

Claim path:

```bash
PYTHONPATH=src conda run -n aiqec python -m scope_static.experiments.run_static --config configs/scope_static/d3_r1_MVP01.yaml
```

MVP04 rank sweep:

```bash
PYTHONPATH=src conda run -n aiqec python -m scope_static.experiments.run_static --config configs/scope_static/d3_r1_MVP04.yaml
```

Diagnostic path:

```bash
PYTHONPATH=src conda run -n aiqec python -m scope_static.experiments.run_static --config configs/scope_static/d3_r3_diagnostic.yaml
```

The default likelihood backend is `auto`. On CUDA tensors it tries the custom C++/CUDA extension first and falls back to the exact PyTorch dynamic program if the extension is unavailable. On CPU tensors it uses PyTorch. Runs record both the requested backend and the resolved backend in `metrics.json`.

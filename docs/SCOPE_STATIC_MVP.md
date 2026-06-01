# SCOPE-Static DEM Fault-Logit MVP

This MVP studies SCOPE-Static at the DEM parity-map level only.
Stage 2 static discovery is specified separately in
`docs/SCOPE_STATIC_DISC.md`.

The learned object is a Bernoulli fault-logit field over a fixed canonicalized detector error model:

```text
e_j ~ Bernoulli(p_j)
y = A e mod 2
A in F_2^{B x M}
```

- `A`: DEM parity map. Column `j` records which observation bits flip when
  effective DEM fault `j` occurs.
- `e in {0,1}^M`: latent effective-fault vector for one shot.
- `y in {0,1}^B`: observed detector/logical bit vector for one shot.
- `B`: number of detector plus logical observable bits.
- `M`: number of effective DEM fault mechanisms after duplicate-mask
  canonicalization.
- `lambda_j = logit(p_j)`: Stage 1 fault logit.
- `O`: number of known orbits.
- `r`: fixed residual feature rank.
- `K_t`: reserved for later SCOPE-Discovery prototype counts.

The graph now keeps sparse parity-map views as the primary scalable interface:

```text
supports_by_fault[j] = observation bits touched by fault j
faults_by_observation_bit[b] = faults touching observation bit b
packed_masks64[j] = 64-bit chunks for exact small-window paths
```

The dense `A` tensor remains as a compatibility artifact for small tests and toy exact-global runs.

## Claim Boundary

This stage may claim evidence about orbit sharing, fixed residual features, exact DEM likelihood, and `d_Q^DEM` inside this fixed Bernoulli parity-map family.

This stage must not claim CPTP/GKSL learning, learned full noisy-circuit Born-rule likelihood from hardware data, context-conditioned amortization, latent quotient discovery, OOD transfer, or temporal drift tracking.

Project-wide, the eventual target is the six-axis physical generation problem:
generation fidelity, interpretability, decoder utility, cross-context
generalization, drift prediction, and identifiability. Stage 1 contributes a
narrow DEM-level slice of generation-fidelity, compression, and known-quotient
evidence only; it does not solve that full physical generation problem.

## Baselines

- `local`: fully independent DEM fault logits with neutral initialization. This is the uncompressed per-effective-fault baseline, not a spatially local model.
- `dmle_qec`: DMLE-QEC-style independent DEM prior-logit MLE baseline. It follows only the compatible Stage-1 slice of [cxMoonGlade/DMLE-QEC](https://github.com/cxMoonGlade/DMLE-QEC): initialize independent DEM priors from the DEM, then optimize those priors by differentiable detector-syndrome NLL. In this package the detector-syndrome NLL is computed by the exact parity-map backend, and learned logits are evaluated with the common Stage-1 metrics. This is not the complete upstream PlanarNet/TensorNetwork/gate-to-DEM implementation.
- `dmle_qec_upstream`: optional direct adapter to `/tmp/DMLE-QEC` using the upstream `TensorNetwork`/`PCM` surface-code DEM MLE path. It is disabled by default and fails closed when the upstream repository or dependencies are unavailable.
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

For scaling beyond toy `B`, the MVP05 path uses local exact windows:

```text
a_{j,W} = a_j restricted to W
```

Each window runs the same exact parity DP over `2^|W|`, not `2^B`. The initial window builders cover single detectors, detector pairs induced by DEM faults, radius-1 detector-coordinate neighborhoods, boundary/logical windows, template motifs, and known-orbit windows.

Detector-rate MAE and local-correlation error use exact parity-moment formulas from sparse supports, so those metrics no longer require the global exact distribution.

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

Every run also writes compression audit fields:

```json
{
  "P_local": 0,
  "P_hard": 0,
  "P_soft": 0,
  "soft_compressed": false,
  "rank_condition_satisfied": false
}
```

This prevents rank-soft runs from being described as compressed when `O(1+r) >= M`.

## S1.6/S1.7 Google DEM Diagnostics

The old Google DEM/static preprocessing-ablation runner, logical-aware window
runner, and summarizer are archived with the Google DEM-proxy diagnostic stack
under `scope_static.archive.experiments.google_gdisc15`. They remain historical
evidence only; they are not the current Google real-data teacher-learner path.

The active Google path keeps the read-only Set1 data readers and builds a frozen
Stage 3 V2 public syndrome-response surface through cache and aggregate stages:

```bash
scope-google-s3-visible-cache-v2 --config configs/scope_static/google_s3_visible_cache_v2.yaml
scope-google-s3-visible-aggregate-v2 --config configs/scope_static/google_s3_visible_aggregate_v2.yaml
scope-google-s3-visible-adapter-v2 --config configs/scope_static/google_s3_visible_adapter_v2.yaml
```

Kernel benchmarks remain available through
`scope_static.experiments.willow_data.benchmark_cuda_kernels`; records include
CPU/PyTorch, CUDA DP, CUDA spectral, and active-window workload audits. A small
metric-reproduction gate is available through
`scope_static.experiments.willow_data.compare_cuda_kernel_variants`.

## Running

From a fresh checkout, install the package in editable mode:

```bash
conda run -n aiqec python -m pip install -e .
```

Then run experiment modules without setting `PYTHONPATH`. In the current WSL/CUDA
setup, exporting `PYTHONPATH` can make PyTorch fail CUDA/NVML discovery even
though `nvidia-smi` sees the RTX 5090.

Claim path:

```bash
conda run -n aiqec python -m scope_static.experiments.static.run --config configs/scope_static/d3_r1_MVP01.yaml
```

MVP03 rank-5 global exact rerun:

```bash
conda run -n aiqec python -m scope_static.experiments.static.run --config configs/scope_static/d3_r1_MVP03.yaml
```

MVP04 rank sweep:

```bash
conda run -n aiqec python -m scope_static.experiments.static.run --config configs/scope_static/d3_r1_MVP04.yaml
```

MVP05 local-window smoke objective:

```bash
conda run -n aiqec python -m scope_static.experiments.static.run --config configs/scope_static/d3_r1_MVP05_windows.yaml
```

MVP05 full local-window sweep:

```bash
conda run -n aiqec python -m scope_static.experiments.static.run --config configs/scope_static/d3_r1_MVP05_windows_full.yaml
```

For small local windows, CPU/PyTorch is usually faster than launching many tiny CUDA-extension kernels. The smoke config is intentionally small; use the full sweep as a long-running evidence job.
The full MVP05 config uses explicit `teacher_cases` to avoid duplicate exact-orbit runs and caches rank-invariant fits for `local`, `dmle_qec`, and `hard_orbit`; only the soft residual is refit per residual rank.

Diagnostic path:

```bash
conda run -n aiqec python -m scope_static.experiments.static.run --config configs/scope_static/d3_r3_diagnostic.yaml
```

The default likelihood backend is `auto`. On CUDA tensors it tries the custom C++/CUDA extension first and falls back to the exact PyTorch dynamic program if the extension is unavailable. On CPU tensors it uses PyTorch. Runs record both the requested backend and the resolved backend in `metrics.json`.

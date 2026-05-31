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

## S1.6 Google Set1 Preprocessing Ablation

S1.6 adds a read-only adapter for
`/home/cx/Document/google_72Q_surface_code_d3_d5_set1`. The adapter accepts
either the outer dataset path or the nested
`google_72Q_surface_code_d3_d5_set1/google_72Q_surface_code_d3_d5_set1` path,
then validates that `sample_00` exists before enumerating leaves.

The new runner is intentionally separate from `run_static`:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.google.static \
  --dataset-root /home/cx/Document/google_72Q_surface_code_d3_d5_set1
```

For a fast real-data smoke:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.google.static \
  --dataset-root /home/cx/Document/google_72Q_surface_code_d3_d5_set1 \
  --train-shots 256 --heldout-shots 256 --max-windows 8 --steps 2 \
  --models hard_orbit \
  --orbit-modes fault_graph_heuristic,schedule_geometric \
  --skip-cross-sample-transfer
```

Cross-sample transfer from `sample_00` to `sample_01` through `sample_20` is
available with `--cross-sample-transfer`.

The Google runner is GPU-first. With CUDA visible, the default `--device auto`
selects `cuda` and the C++/CUDA `cuda_extension` backend. Use `--native-gpu`
when the run must fail instead of falling back. CPU execution is allowed only
when requested explicitly with `--allow-cpu-fallback`.
Terminal output is concise by default and prints only the final coverage,
heldout model comparison, transfer means, and decision summary. Use `--progress-json`
when per-stage JSON progress events are needed for profiling or automation.

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.google.static \
  --dataset-root /home/cx/Document/google_72Q_surface_code_d3_d5_set1 \
  --train-shots 5000 --heldout-shots 2000 --max-windows 32 --steps 50 \
  --models hard_orbit,soft_feature_orbit \
  --orbit-modes fault_graph_heuristic,schedule_geometric \
  --output-dir outputs/google_static/S1_6_native_gpu
```

The CUDA path uses a batched exact local-window training kernel. By default the
Google runner uses `--cuda-kernel-variant auto`, which keeps the DP kernel for
larger windows and selects the active-fault Walsh/Fourier spectral kernel for
small exact windows whose prepared workload fits the memory cap. Pass
`--cuda-kernel-variant dp` for conservative DP-only reproduction runs.
Detached evaluation and transfer use a forward-only CUDA kernel, so they do not
build gradient history or run the backward adjoint. The runner streams JSON
progress events with fit/evaluation wall times. Prepared local-window
state/count caches are persisted by default under `<output-dir>/prepared_cache`; use
`--prepared-cache-dir` to share them across output directories or
`--disable-prepared-cache` for one-off uncached runs.

The training kernel can be audited with
`--cuda-kernel-variant spectral_shadow`. This computes both the current DP
kernel and the new active-fault Walsh/Fourier spectral kernel, returns the DP
result, and fails on loss/gradient mismatch.

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.google.static \
  --dataset-root /home/cx/Document/google_72Q_surface_code_d3_d5_set1 \
  --native-gpu \
  --cuda-kernel-variant spectral_shadow \
  --train-shots 512 --heldout-shots 256 --max-windows 8 --steps 2 \
  --models hard_orbit \
  --orbit-modes fault_graph_heuristic \
  --skip-cross-sample-transfer \
  --output-dir outputs/google_static/S1_6_spectral_shadow_smoke
```

Kernel benchmarks are available through
`scope_static.experiments.google.benchmark_cuda_kernels`; records include CPU/PyTorch,
CUDA DP, CUDA spectral, and active-window workload audits. A small
metric-reproduction gate is available through
`scope_static.experiments.google.compare_cuda_kernel_variants`.

The default leaf is `sample_00/d3_at_q5_5/X/r13` with `decoder_si1000`.
Observations are loaded as `torch.bool[N, B] = [detection_events |
obs_flips_actual]`.

S1.6 builds a minimal `GoogleScheduleContext` proxy for
`c = (H_sched, u, kappa, tau)`. It records hardware layout, qubit roles and
coordinates, TICK/layer schedule, gate instances, detector and observable
definitions, `.b8` paths, metadata, sample/order proxies, code descriptor, and
coverage checks. This object is a minimal `H_sched` proxy, not a full
`Aut(H_sched)` solver.

The preprocessing modes are:

- `local`: singleton DEM-fault orbits.
- `fault_graph_heuristic`: current DEM-mask geometry heuristic for `omega(j)`.
- `schedule_geometric`: coordinate/schedule-derived candidate symmetries,
  validated against effective DEM fault columns.

Claim boundary: `schedule_geometric` is an audited schedule-derived
preprocessing proxy. It is not a full hardware automorphism solver, not full
SCOPE-Twin, and not CPTP/GKSL learning. It only tests whether schedule-derived
coloring gives a better fixed quotient/orbit prior than the current DEM-mask
geometry heuristic. S1.6 still induces orbits over effective DEM fault columns,
not true hardware/schedule fault locations.

The runner emits provenance, schedule-coverage, symmetry-validation, partition,
window, model, residual, heldout, and optional cross-sample transfer audits.
`schedule_symmetry_status` is one of `nontrivial`, `identity_only`, or
`invalid`; `identity_only` is a valid empirical outcome, not a code failure. It
also records a tiny synthetic audit comparing local-window NLL to global exact
NLL in a `B=3` case where global exact is feasible.

Decision rule: schedule preprocessing is useful only when it produces
nontrivial accepted symmetries and matches or improves heldout/transfer metrics
at equal or fewer parameters, or gives a clearer stable quotient with comparable
metrics. If only identity survives, record that the DEM-mask `FaultGraph`
heuristic is sufficient for Stage-1 Google validation.

## S1.7 Logical-Aware Window Plan

S1.7 keeps the S1.6 Google data path but changes the default local-window plan
from detector-local to logical-aware. The runner now defaults to
`--window-plan-mode logical_aware`, which adds deduplicated logical observable
windows before any family budget is applied:

- `logical_single`: the logical observable bit alone.
- `logical_fault_support`: the full DEM support of each effective fault that
  touches a logical observable bit, deduplicated by sorted bit-set key.
- `logical_detector_pair`: detector/logical two-bit marginals not already
  represented by exact logical fault supports.

Family budgets replace global truncation in this mode:

```text
single_detector: all
detector_pair: 64
logical_single: all
logical_detector_pair: 64
logical_fault_support: all
```

This prevents `--max-windows` from silently dropping the logical bit. The
previous detector-local plan is still available with
`--window-plan-mode detector_local`.

Window audits now report logical coverage, raw/unique logical fault-support
counts, duplicates removed, windows containing logical bits, logical family
counts, and the fraction of logical fault supports represented by exact logical
windows.

Real-data metrics split local-window evidence into combined, detector, logical,
logical-single, logical-fault-support, and logical-detector-pair groups. Each
group reports:

```text
model_window_nll
heldout_empirical_window_entropy
excess_window_nll = model_window_nll - heldout_empirical_window_entropy
num_windows
mean_window_bits
```

Raw NLL values are cross-entropies in nats per local window and should not be
compared across different window plans without their empirical entropy
baselines. `excess_window_nll` is the preferred real-data evidence metric when
no oracle teacher distribution exists.

Because S1.7 excess values are often close to zero, Google records also include
paired comparison fields against the uncompressed `local` baseline:

```text
excess_mnats_per_window = 1000 * excess_window_nll
excess_delta_mnats_vs_baseline = 1000 * (model_excess - local_excess)
pseudo_delta_bits_per_shot_vs_baseline
combined_excess_parameter_pareto_status
```

The pseudo per-shot delta multiplies the mean window excess gap by the number
of windows and converts nats to bits. It is a diagnostic scale for the
local-window pseudo-likelihood, not a global exact likelihood. The Pareto
status compares combined excess NLL against parameter count, so compressed
models can be credited when they trade a tiny evidence gap for a large
parameter reduction.

Existing result files can be re-summarized without rerunning Google data:

```bash
conda run -n aiqec python -m scope_static.experiments.google.summarize_static \
  outputs/google_static/S1_7_logical_aware_full_clean/google_static_metrics.json \
  --preprocessing-mode fault_graph_heuristic
```

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

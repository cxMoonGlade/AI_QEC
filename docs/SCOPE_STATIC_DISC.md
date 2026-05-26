# SCOPE-Static Discovery MVP

This document defines Stage 2 for the static SCOPE path.

`docs/SCOPE_STATIC_MVP.md` is the Stage 1 document: it studies fixed-context
DEM fault-logit learning when the orbit map is known. This document is Stage 2:
it keeps the same fixed-context DEM likelihood, but asks whether the model can
discover the sharing structure instead of receiving the orbit map by hand.

## Goal

Stage 2 answers:

```text
Can observations identify hidden sharing structure?
```

Stage 1 used a known DEM-fault orbit map:

```text
omega(j) = known orbit id for effective DEM fault j
```

Stage 2 withholds that map from the learner and replaces it with a learned
assignment:

```text
S[j, k] = learned assignment weight of DEM fault j to prototype k
```

Use `S` or `Pi` for learned assignments. Do not use `A`; `A` is reserved for
the DEM parity map.

## Claim Boundary

This stage may claim evidence about:

- latent quotient/orbit recovery in the fixed DEM/Bernoulli family.
- assignment recovery on synthetic teachers with known hidden partitions.
- held-out likelihood and calibration after replacing known orbits with learned
  prototypes.
- robustness of discovery across seeds, shot budgets, and prototype counts.

This stage must not claim:

- CPTP/GKSL physical-channel learning.
- full noisy-circuit Born-rule likelihood.
- context-conditioned amortization.
- temporal drift tracking.
- real-hardware ground-truth orbit recovery from Google data.

Google repetition-code and surface-code datasets can be used as empirical
external validation later, but they do not provide true hidden fault partitions.
They cannot support ARI/NMI claims unless a proxy partition is explicitly
defined.

## Static DEM Contract

Stage 2 keeps the Stage 1 parity-map likelihood:

```text
e_j ~ Bernoulli(p_j)
p_j = sigmoid(lambda_j)
y = A e mod 2
A in F_2^{B x M}
```

`B` is the number of detector plus logical observable bits. `M` is the number of
effective DEM fault mechanisms after duplicate-mask canonicalization.

The sparse parity-map views remain the scalable interface:

```text
supports_by_fault[j] = observation bits touched by fault j
faults_by_observation_bit[b] = faults touching observation bit b
packed_masks64[j] = 64-bit chunks for exact small-window paths
```

Dense `A` is only a compatibility artifact for small tests and toy global exact
runs.

## Discovery Model

The first Stage 2 MVP is DEM-fault-level discovery:

```text
S in [0, 1]^{M x K}
sum_k S[j, k] = 1
```

where `K` is the number of discovered prototypes. The learned fault logit field
is:

```text
lambda_j = sum_k S[j, k] alpha_k
```

This is the discovery analogue of Stage 1 hard orbit sharing. A soft-residual
extension may use:

```text
lambda_j = sum_k S[j, k] (alpha_k + beta_k^T phi_j)
```

where `phi_j` is a centered fault-level residual feature. The feature-centering
audit from Stage 1 still applies when soft residuals are enabled.

The full SCOPE-Twin object eventually learns location/template assignments:

```text
S^{(t)} in [0, 1]^{|I_t| x K_t}
```

That is the later physical-location version. The Stage 2 static MVP should start
at DEM-fault level because it directly reuses the validated Stage 1 graph,
likelihood, sparse supports, windows, and metrics.

## Parameter Accounting

Every discovery run must report parameter counts separately for:

```json
{
  "P_local": 0,
  "P_known_hard_orbit": 0,
  "P_discovery_prototypes": 0,
  "P_discovery_assignment": 0,
  "P_discovery_total": 0,
  "assignment_parameterization": "free|feature_conditioned|template_conditioned",
  "compressed_claim_allowed": false
}
```

Free per-fault assignment logits cost approximately `M * (K - 1)` parameters.
Therefore a free-assignment discovery model is usually an identifiability probe,
not a compression claim. Compression claims are only allowed when the assignment
parameterization itself is compressed, for example by a feature-conditioned or
template-conditioned assignment network with audited parameter count.

## Likelihood

Use the same exact DEM likelihood family as Stage 1.

For small `B`, the global exact parity dynamic program may be used. For larger
systems, use the MVP05 local-window path:

```text
a_{j,W} = a_j restricted to W
```

Each window runs exact parity DP over `2^|W|`, not `2^B`.

Detector-rate MAE and local-correlation error should use exact parity-moment
formulas from sparse supports where possible, so they do not require materializing
the global exact distribution.

## Synthetic Teachers

Stage 2 must be tested first on synthetic teachers where the hidden partition is
known but withheld from the model.

Required teacher cases:

- `exact_orbit`: logits are constant inside the hidden partition.
- `in_family_soft_residual`: logits are prototype plus in-family centered
  residual features.
- `out_of_family_residual`: logits include residual structure not represented by
  the selected soft feature family.

The learner must receive observations and DEM structure, but not the true
`omega(j)` labels. The evaluator may use the hidden labels for ARI/NMI only.

## Metrics

Every Stage 2 synthetic run should report:

```json
{
  "ari": 0.0,
  "nmi": 0.0,
  "assignment_entropy_mean": 0.0,
  "num_active_prototypes": 0,
  "heldout_nll": 0.0,
  "delta_nll_oracle": 0.0,
  "d_q_dem": 0.0,
  "detector_rate_mae": 0.0,
  "local_correlation_error": 0.0,
  "tvd": null
}
```

`TVD` is only required when the global exact distribution is small enough to
materialize.

Run summaries must aggregate these metrics across seeds by teacher case, shot
budget, and `K`.

## Guardrails

Discovery is more failure-prone than known-orbit fitting. Every run should audit:

- assignment collapse: all faults assigned to one prototype.
- dead prototypes: prototypes with near-zero mass.
- label switching: compare partitions with permutation-invariant metrics only.
- over-specified `K`: extra prototypes should be inactive or harmless.
- under-specified `K`: likelihood should degrade and ARI/NMI should expose the
  mismatch.
- train/heldout gap: discovery should not only memorize low-shot samples.
- compression honesty: free assignments are not automatically compressed.

## Stage 2A Exit Criteria

Stage 2A is ready when synthetic discovery shows:

- high ARI/NMI on `exact_orbit` teachers when `K` matches the true number of
  orbits.
- held-out NLL close to the known-orbit hard baseline on `exact_orbit` teachers.
- degraded but interpretable behavior when `K` is too small or too large.
- seed-aware summaries over multiple seeds and shot budgets.
- no assignment-collapse failures in the main claim runs.
- parameter accounting that clearly separates prototype parameters from
  assignment parameters.

Only after these conditions pass should Google repetition-code and surface-code
datasets be used as Stage 2B real-hardware empirical validation.

## Stage 2B External Validation

Google datasets are useful for external validation, not oracle discovery.

They provide:

```text
measurements.b8
detection_events.b8
obs_flips_actual.b8
circuit_ideal.stim
circuit_noisy_si1000.stim
metadata.json
decoding_results/*/error_model.dem
decoding_results/*/obs_flips_predicted.b8
```

They do not provide the true hidden physical fault mechanism or true orbit
partition. Use them to evaluate held-out detector/logical likelihood, detector
rate matching, local correlation matching, logical prediction, calibration
transfer, and robustness across samples or time. Do not use them to claim true
latent partition recovery unless the partition is explicitly defined as a proxy.

The Google runner can include Stage 2 discovery models in the same S1.7
logical-aware comparison:

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

Records for `disc_hard` and `disc_soft` report assignment entropy, active/dead
prototype audits, free-assignment parameter accounting, and local-baseline
excess-NLL deltas. They intentionally report that ground-truth partition
recovery is unavailable on Google data.

## Planned Run Shape

Recommended first config:

```text
configs/scope_static/d3_r1_STAGE2A_full.yaml
```

Recommended first output folder:

```text
outputs/scope_static/STAGE2A_full/
```

The first implementation should reuse:

- Stage 1 `FaultGraph`.
- sparse parity supports.
- local-window likelihood.
- seed-aware result aggregation.
- Stage 1 baselines: `local`, `dmle_qec`, `hard_orbit`,
  `soft_feature_orbit`.

The new Stage 2 baselines are:

- `disc_hard`: learned assignment plus prototype logits.
- `disc_soft`: learned assignment plus prototype logits and centered residual
  features.
- `known_hard_orbit`: Stage 1 hard orbit using the hidden labels, used only as
  an oracle baseline.
- `known_soft_feature_orbit`: Stage 1 soft feature orbit using the hidden
  labels, used only as an oracle baseline.

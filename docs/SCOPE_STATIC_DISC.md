# SCOPE-Static Discovery

This document defines Stage 2 for the static SCOPE path.

Stage 1, defined in `docs/SCOPE_STATIC_MVP.md`, studies fixed-context
DEM/Bernoulli fault-logit learning when the DEM-fault orbit map is known.
Stage 2 keeps the same fixed-context DEM likelihood, but asks whether sharing
structure can be discovered instead of supplied by hand.

The central question is:

```text
Can observations identify hidden DEM-fault sharing structure?
```

Stage 1 used a known orbit map:

```text
omega(j) = known orbit id for effective DEM fault j
```

Stage 2 withholds that map from the learner and replaces it with a learned
assignment:

```text
S[j, k] = learned assignment weight of DEM fault j to prototype k
```

Use `S` or `Pi` for learned assignments. Do not use `A` for assignments; `A`
is reserved for the DEM parity map.

## Roadmap

Stage 2 is split into deliberately separate tracks:

```text
Stage 2A.0: Current free-assignment synthetic test
  Question: Does free per-fault S recover hidden omega(j)?

Stage 2A.0.5: Passive identifiability audit
  Question: Do visible non-leaking fault signatures already separate omega(j)?

Stage 2A.1: Proposed hardening study
  Question: Can recovery-biased optimization fix free-S recovery failures?

Stage 2A.2: Proposed identifiability-aware discovery
  Question: Can probe design, OT constraints, or multi-environment invariance
            make quotient recovery identifiable?

Stage 2C: Local inverse representation discovery
  Question: Can fitted local inverse logits or response fingerprints be
            denoised, factorized, and clustered better than direct S/alpha
            likelihood learning?

Stage 2D: Active local-logit observability
  Question: Which probes improve recoverability of local inverse logits and
            their mechanism clusters?

Stage 2E: full-circuit CUDA-Q physical-teacher gate
  Question: Can literal n-qubit noisy circuits at configured depth produce
            PHYC1 data, PHYC2 teacher self-distinguishment, and PHYC3
            no-leakage learner recovery with high-quality quantum/readout
            error estimates?

Stage 2B: Google external validation
  Question: On real data without true omega(j), do discovery models improve
            likelihood, calibration, transfer, or decoder-facing utility?
```

Do not merge these tracks in reports. A Stage 2A.1 or Stage 2A.2 result is not
retroactive evidence that the Stage 2A.0 free-assignment test succeeded.

## Claim Boundary

Stage 2 may claim evidence about:

- latent quotient/orbit recovery in the fixed DEM/Bernoulli family.
- assignment recovery on synthetic teachers with known hidden partitions.
- heldout likelihood and calibration after replacing known orbits with learned
  prototypes.
- robustness of discovery across seeds, shot budgets, prototype counts, and
  synthetic identifiability stressors.

Stage 2 must not claim:

- CPTP/GKSL physical-channel learning.
- learned full noisy-circuit Born-rule likelihood from hardware data.
- context-conditioned amortization as part of Stage 2A.0.
- temporal drift tracking as part of Stage 2A.0.
- real-hardware ground-truth orbit recovery from Google data.

Project-wide, the eventual target is the six-axis physical generation problem:
generation fidelity, interpretability, decoder utility, cross-context
generalization, drift prediction, and identifiability. Stage 2 addresses the
identifiability and early interpretability slices under controlled static or
synthetic catalog-validation settings; it is not yet evidence that a CPTP/GKSL
physical generation model holds across all six axes.

Google repetition-code and surface-code datasets can be used later as empirical
external validation, but they should remain outside the first Stage 3 discovery
claim unless the project explicitly moves beyond the current controlled
physical-mechanism catalog. They do not provide true hidden fault partitions and
cannot support true ARI/NMI recovery claims unless a proxy partition is
explicitly defined and labelled as a proxy.

## Static DEM Contract

Stage 2 keeps the Stage 1 parity-map likelihood:

```text
e_j ~ Bernoulli(p_j)
p_j = sigmoid(lambda_j)
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
- `lambda_j`: Stage 1 fault logit, `logit(p_j)`.

The sparse parity-map views remain the scalable interface:

```text
supports_by_fault[j] = observation bits touched by fault j
faults_by_observation_bit[b] = faults touching observation bit b
packed_masks64[j] = 64-bit chunks for exact small-window paths
```

Dense `A` is only a compatibility artifact for small tests and toy global exact
runs.

## Shared Discovery Model

The Stage 2 DEM-fault discovery object is:

```text
S in [0, 1]^(M x K)
sum_k S[j, k] = 1
```

where `K` is the number of discovered prototypes.

The hard discovery field is:

```text
lambda_j = sum_k S[j, k] alpha_k
```

The soft-residual extension is:

```text
lambda_j = sum_k S[j, k] (alpha_k + beta_k^T phi_j)
```

`disc_soft` is allowed only when `phi_j` is learner-visible. Features must not
be selected, centered, target-encoded, or otherwise constructed using hidden
`omega(j)`. Hidden `omega(j)` is available only to the synthetic teacher and
the evaluator.

The free per-fault assignment table is an identifiability probe, not a
compression architecture. Compression claims require a compressed assignment
parameterization, such as a feature-conditioned or template-conditioned
assignment network, with audited parameter count.

The full SCOPE-Twin object eventually learns location/template assignments:

```text
S^(t) in [0, 1]^(|I_t| x K_t)
```

That is a later physical-location/context-conditioned object. Stage 2 static
discovery stays at DEM-fault level.

## Parameter Accounting

Every discovery run must report:

```json
{
  "P_local": 0,
  "P_known_hard_orbit": 0,
  "P_known_soft_feature_orbit": 0,
  "P_discovery_prototypes": 0,
  "P_discovery_assignment": 0,
  "P_discovery_total": 0,
  "assignment_parameterization": "free",
  "compressed_claim_allowed": false
}
```

For a free assignment table, assignment logits cost approximately:

```text
M * (K - 1)
```

Free assignments are therefore usually an identifiability probe, not evidence
of compression.

## Shared Metrics

Synthetic Stage 2 runs should report:

```json
{
  "ari": 0.0,
  "nmi": 0.0,
  "assignment_entropy_mean": 0.0,
  "assignment_entropy_normalized": 0.0,
  "prototype_masses": [],
  "num_active_prototypes": 0,
  "num_dead_prototypes": 0,
  "assignment_collapse": false,
  "heldout_nll": 0.0,
  "known_orbit_oracle_model": "known_hard_orbit",
  "delta_nll_known_orbit": 0.0,
  "d_q_dem": 0.0,
  "detector_rate_mae": 0.0,
  "local_correlation_error": 0.0,
  "tvd": null
}
```

`TVD` is required only when the global exact distribution is small enough to
materialize.

ARI/NMI are computed from:

```text
hat_omega(j) = argmax_k S[j, k]
```

Hard labels are used only for evaluation. Label switching is expected, so
partition metrics must be permutation-invariant.

## Stage 2A.0 Current Free-Assignment Test

Stage 2A.0 is the current implemented synthetic identifiability test.

It asks:

```text
Can a free per-fault assignment matrix S[j,k] recover hidden omega(j) from
DEM parity-map observations alone?
```

The learner sees:

- the fixed DEM parity map `A`.
- sampled observations `y`.
- learner-visible DEM/fault features where applicable.

The learner does not see:

- hidden `omega(j)`.
- hidden-orbit-centered `phi`.
- teacher prototype labels.

The evaluator may use hidden `omega(j)` for ARI/NMI only.

### Implemented Models

The Stage 2A.0 model set is:

- `disc_hard`: free `S[j,k]` plus prototype logits `alpha_k`.
- `disc_soft`: free `S[j,k]` plus learner-visible residual features.
- `known_hard_orbit`: synthetic-only known-orbit oracle.
- `known_soft_feature_orbit`: synthetic-only known soft-feature oracle.
- `local`: unshared fault-logit baseline.
- `dmle_qec`: detector-only baseline.

Discovery runs use multiple restarts. The selected restart is the one with the
lowest training NLL. All restart outcomes are recorded, including collapse,
dead prototypes, entropy, ARI/NMI, and poor-recovery flags.

### Synthetic Teachers

Required teacher families:

- `exact_orbit`: logits are constant inside hidden `omega(j)`.
- `exact_orbit_separated`: exact-orbit teacher with stronger prototype logit
  separation for controlled identifiability stress.
- `in_family_soft_residual`: prototype plus in-family centered residual.
- `in_family_soft_residual_separated`: separated prototype plus in-family
  residual.
- `out_of_family_residual`: residual structure not represented by the selected
  soft feature family.
- `out_of_family_residual_separated`: separated prototype plus out-of-family
  residual.

Separated teachers are controlled synthetic probes. They are not hardware
claims.

### Success Rule

Stage 2A.0 success is two-dimensional:

```text
success = high partition recovery AND high predictive quality
```

Concretely:

- high ARI/NMI against hidden `omega(j)`.
- heldout NLL close to the matched known-orbit oracle.
- no selected main-claim run collapses.
- `K` sweep behavior is interpretable:
  - `K < O`: recovery and NLL should degrade.
  - `K = O`: recovery should be strongest.
  - `K > O`: extra prototypes should become inactive or harmless.

NLL-only success is not sufficient. ARI/NMI-only success is not sufficient.

If heldout NLL is close to the known-orbit oracle but ARI/NMI are low, Stage
2A.0 found a good DEM-fault logit representation but did not recover the hidden
quotient. This should be reported as:

```text
likelihood-positive, recovery-negative
```

### Current Run

Recommended Stage 2A.0 config:

```text
configs/scope_static/d3_r1_STAGE2A_full.yaml
```

Recommended output folder:

```text
outputs/scope_static/STAGE2A_full/
```

Run:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.static.discovery \
  --config configs/scope_static/d3_r1_STAGE2A_full.yaml
```

The terminal summary should stay compact. Do not print the full `metrics.json`
to the terminal.

Summarize the completed Stage 2A.0 run:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.static.stage2a0_summary \
  --metrics outputs/scope_static/STAGE2A_full/metrics.json
```

This writes:

```text
outputs/scope_static/STAGE2A_full/stage2a0_summary.json
outputs/scope_static/STAGE2A_full/stage2a0_summary.md
```

## Stage 2A.0.5 Passive Identifiability Audit

Stage 2A.0.5 is a diagnostic audit, not a likelihood-recovery claim.

It asks:

```text
Do visible, non-leaking fault signatures contain enough information to separate
the synthetic hidden quotient before Stage 2A.1 hardening?
```

A positive DISC10 result means:

```text
Passive visible signatures contain enough information to separate the synthetic
hidden quotient.
```

It does not mean physical mechanism discovery, and it does not prove the
likelihood learner can recover `omega(j)`.

### DISC10 Moment/Spectral Seed

DISC10 constructs fault-level signatures using only:

- the DEM parity map `A`.
- visible detector/logical observations.
- visible detector coordinates or geometry.
- visible fault support structure.

It must not use hidden fault activations, hidden `omega(j)`, hidden-orbit
centered `phi`, or ARI/NMI for selecting signatures or hyperparameters.

The first pass uses:

```json
{
  "K_mode": "known_K_synthetic_audit",
  "ari_nmi_used_for_selection": false,
  "selection_rule": "observable_only"
}
```

Signature families currently include:

- `structural`.
- `local_logit`.
- `moment_spectral`.
- `combined`.

Run:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.static.identifiability \
  --config configs/scope_static/d3_r1_STAGE2A_DISC10_passive_audit.yaml
```

This writes:

```text
outputs/scope_static/STAGE2A_DISC10_passive_audit/disc10_metrics.json
outputs/scope_static/STAGE2A_DISC10_passive_audit/disc10_summary.md
outputs/scope_static/STAGE2A_DISC10_passive_audit/signatures/*.npy
outputs/scope_static/STAGE2A_DISC10_passive_audit/clusters/*_clusters.json
```

DISC10 output is split into:

```json
{
  "disc10_audit": {
    "best_visible_signature_family": "...",
    "ari": 0.0,
    "nmi": 0.0,
    "active_clusters": 0,
    "passive_identifiability_result": "separates|weak|failed"
  },
  "disc10_seed_candidate": {
    "recommended_for_stage2a1_init": true,
    "signature_family": "...",
    "selection_rule": "observable_only"
  }
}
```

Classification uses the predefined `separates|weak|failed` thresholds and
requires scores to be meaningfully above random/shuffled controls.

## Stage 2A.1 Proposed Hardening Study

Stage 2A.1 is a proposed follow-on study, not part of the Stage 2A.0 claim.

It asks:

```text
Can stronger recovery-biased optimization recover omega(j) when the free
soft-assignment likelihood fit does not?
```

This stage is triggered when Stage 2A.0 is likelihood-positive but
recovery-negative.

Allowed Stage 2A.1 interventions include:

- DISC10/local-logit warm starts that fit visible signatures from observations
  and initialize prototypes without hidden `omega(j)`.
- temperature annealing for `S[j,k]`.
- straight-through or hard-assignment variants.
- alternating hard-assignment updates.
- row-entropy penalties.
- light prototype-mass balancing.
- prototype separation penalties.
- stricter residual control for `disc_soft`, including beta norm or sparsity
  audits.

The first Stage 2A.1 ablation grid is:

```text
A. free random-init disc_hard
B. free local-logit-init disc_hard
C. hard/ST random-init disc_hard
D. hard/ST local-logit-init disc_hard
E. hard/ST local-logit-init + entropy annealing
F. hard/ST local-logit-init + entropy annealing + balance
G. hard/ST local-logit-init + entropy annealing + balance + prototype separation
```

Main comparisons:

```text
A -> B: Does audited initialization help?
B -> D: Does hard assignment help?
D -> E/F/G: Do recovery-biased regularizers help beyond initialization?
```

These interventions must be reported as a different training regime or
assignment parameterization:

```json
{
  "stage2a_variant": "hardening_study",
  "assignment_parameterization": "free_hardened",
  "assignment_initializer": "local_kmeans",
  "uses_hidden_omega_for_initialization": false
}
```

Stage 2A.1 must preserve the original claim boundary:

- hidden `omega(j)` must not be used by the learner, initializer, feature
  selection, or objective.
- ARI/NMI may use hidden `omega(j)` only in the evaluator, and must not select
  initializers, restarts, checkpoints, or hyperparameters.
- selected runs must use validation NLL and observable health checks, not
  recovery metrics.
- NLL-only success still does not count as quotient recovery.
- initializer and hardening schedules must be included in training audits and
  restart records.

Stage 2A.1 acceptance categories:

```text
strong_recovery:
  ARI >= 0.80 and NMI >= 0.80
  delta_nll_known_orbit <= threshold_epsilon
  active clusters >= K - 1
  selected by validation NLL / observable health, not ARI/NMI

partial_recovery:
  ARI or NMI improves substantially over Stage 2A.0 and DISC10
  but does not reach strong recovery threshold

failure:
  NLL remains good but ARI stays low
  or recovery would require ARI/NMI-based run selection
```

Before closing Stage 2A.1, report an assignment movement audit:

```text
init_final_assignment_nmi
fraction_rows_changed
mean_assignment_entropy_start
mean_assignment_entropy_end
assignment_logit_grad_norm
prototype_param_delta_norm
cluster_mass_start
cluster_mass_end
selection_score
selected_by_ari_nmi = false
```

This distinguishes three cases:

- the DISC10/local-logit partition is a stable passive ceiling.
- assignments barely moved after initialization.
- validation/health selection repeatedly selected the same initialized
  partition.

Run:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.static.hardening \
  --config configs/scope_static/d3_r1_STAGE2A1_hardening.yaml
```

`disc_soft` in Stage 2A.1 is primarily a predictive extension unless it also
recovers the hidden partition. If `disc_soft` improves NLL while ARI/NMI remain
poor, it is evidence for residual predictive modeling, not quotient recovery.

## Stage 2A.2 Identifiability-Aware Quotient Discovery

Stage 2A.2 is a proposed research extension based on `docs/S2A-newIdeas.md`.
It is separate from both the current free-assignment test and the hardening
study.

It asks:

```text
Can the experiment or assignment structure be designed so the quotient becomes
more identifiable from observations?
```

Stage 2A.2 should start only after Stage 2A.0 and DISC10 have been reported,
and Stage 2A.1 has clarified whether hardening alone is enough.

The first Stage 2A.2 experiment is:

```text
DISC12_multi_env_shared_assignment
```

Core hypothesis:

```text
Single-environment passive observations are weakly identifying.
The hidden quotient may become identifiable when the same assignment S is
observed across multiple environments with different prototype strengths.
```

Model:

```text
shared:
  S[j, k]

environment-specific:
  alpha[e, k]

fault rate:
  lambda[e, j] = sum_k S[j, k] alpha[e, k]
```

The invariant is the shared quotient assignment. The environment-specific
prototype rates vary.

DISC12 must report:

```json
{
  "stage": "stage2A.2",
  "experiment": "DISC12_multi_env_shared_assignment",
  "uses_hidden_omega_for_training": false,
  "uses_hidden_omega_for_initialization": false,
  "uses_hidden_omega_for_checkpoint_selection": false,
  "uses_hidden_omega_for_final_evaluation": true,
  "ari_nmi_used_for_selection": false
}
```

Initial controlled environments:

```text
env_0: base alpha
env_1: alpha scaled by group-specific factors
env_2: sparse boosted subset of prototypes
env_3: support-size-dependent perturbation
env_4: mixed perturbation
```

Use `env_0` through `env_3` for shared-S training and `env_4` as the heldout
environment. Heldout-environment evaluation freezes learned `S` and adapts only
the new environment's `alpha`.

Baselines:

```text
single_env_free_assignment
single_env_local_logit_init
multi_env_independent_S_per_env
multi_env_shared_S_random_init
multi_env_shared_S_DISC10_init
known_orbit_oracle_shared_S
local_full_per_fault_per_env
```

The key comparison is:

```text
multi_env_shared_S_DISC10_init
vs
single_env_local_logit_init
```

Acceptance categories:

```text
strong_recovery:
  ARI >= 0.80
  NMI >= 0.80
  active clusters >= K - 1
  delta_nll_known_orbit remains small
  no ARI/NMI-based selection

partial_recovery:
  ARI/NMI clearly improve over the Stage 2A.1 ceiling
  but fail strong threshold

predictive_only:
  NLL improves over baselines
  ARI remains low

failure:
  no meaningful recovery or likelihood benefit
```

The current Stage 2A.1 ceiling is:

```text
ARI ~= 0.2748
NMI ~= 0.7097
```

Critical diagnostic:

```text
alpha_variation_norm
between_env_rate_contrast
per_prototype_alpha_separation
shared_assignment_entropy
assignment_movement_from_init
env_holdout_dNLL
```

Run:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.static.multi_env_discovery \
  --config configs/scope_static/d3_r1_STAGE2A2_DISC12_multi_env.yaml
```

Outputs:

```text
outputs/scope_static/STAGE2A2_DISC12_multi_env/metrics.json
outputs/scope_static/STAGE2A2_DISC12_multi_env/disc12_summary.md
outputs/scope_static/STAGE2A2_DISC12_multi_env/shared_assignment.json
outputs/scope_static/STAGE2A2_DISC12_multi_env/env_alpha.json
outputs/scope_static/STAGE2A2_DISC12_multi_env/run_selection_audit.json
outputs/scope_static/STAGE2A2_DISC12_multi_env/contrast_sweep.json
```

The initial DISC12a result should be recorded as:

```text
DISC12a_multi_env_shared_assignment:
  multi_env_predictive_only
  weak_recovery_gain_over_stage2a1
  observable_contrast_likely_insufficient
```

DISC12b adds a contrast-strength sweep:

```text
DISC12b_multi_env_contrast_sweep
```

Question:

```text
Does quotient recovery improve monotonically when environment-induced observable
contrast increases?
```

Sweep either default perturbations or a codebook-style environment design:

```text
contrast_strength in {1x, 2x, 4x, 8x, 16x}
alpha[e, k] = alpha_base[k] + gamma * code[e, k]
```

where `code[e,k]` is a normalized synthetic sign/codebook pattern. This remains
synthetic-only and does not expose hidden `omega(j)` to the learner.

DISC12b tracks:

```text
contrast_strength
between_env_rate_contrast
mean_per_prototype_alpha_separation
singular values of the environment x fault-rate matrix
ARI/NMI of shared S
delta_nll_known_orbit
env_holdout_dNLL
active clusters
assignment_movement_from_init
```

Decision rules:

```text
If ARI/NMI increase with observable contrast:
  conclusion = quotient is identifiable under sufficient environment contrast.

If NLL improves but ARI remains low even at high contrast:
  conclusion = shared predictive structure differs from teacher omega.

If contrast sweep fails to increase observable contrast:
  conclusion = environment generator is too weak or perturbations are attenuated.

If high observable contrast exists but recovery still fails:
  conclusion = model/optimization or assignment parameterization remains insufficient.
```

### DISC13 Observational Quotient Audit

DISC13 is the target-alignment gate after DISC12b.

It asks:

```text
Is hidden teacher omega(j) actually the right recoverable target under the
current DEM/Bernoulli observation map?
```

DISC13 is evaluator-only:

```json
{
  "stage": "stage2A.2",
  "experiment": "DISC13_observational_quotient_audit",
  "uses_hidden_omega_for_training": false,
  "uses_hidden_omega_for_initialization": false,
  "uses_hidden_omega_for_checkpoint_selection": false,
  "uses_hidden_omega_for_final_evaluation": true,
  "ari_nmi_used_for_selection": false
}
```

It constructs observational quotients from teacher response fingerprints, then
compares:

```text
hidden omega
learned partition
observational quotient
```

Primary target-audit comparison:

```text
ARI(observational_quotient, omega)
ARI(learned_partition, omega)
ARI(learned_partition, observational_quotient)
```

If learned partitions align better with the observational quotient than hidden
`omega`, target mismatch is confirmed. If the observational quotient itself is
close to hidden `omega` but learned recovery remains low, the target is not the
main problem and active probe design becomes the next credible step.

Run:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.static.observational_quotient \
  --config configs/scope_static/d3_r1_STAGE2A2_DISC13_observational_quotient.yaml
```

Outputs:

```text
outputs/scope_static/STAGE2A2_DISC13_observational_quotient/metrics.json
outputs/scope_static/STAGE2A2_DISC13_observational_quotient/disc13_summary.md
outputs/scope_static/STAGE2A2_DISC13_observational_quotient/observational_quotient.json
outputs/scope_static/STAGE2A2_DISC13_observational_quotient/target_alignment.json
outputs/scope_static/STAGE2A2_DISC13_observational_quotient/fingerprints/*.npy
```

Current result:

```text
target_mismatch_not_confirmed
oracle_parameter_space_contains_hidden_quotient
passive_observation_training_signal_still_fails_to_isolate_target
```

Key evidence:

```text
oracle_logit:
  ARI 1.0000
  NMI 1.0000

observation_side:
  ARI 0.2538
  NMI 0.7058

combined:
  ARI 0.3422
  NMI 0.7594

learned vs omega:
  ARI 0.3574
  NMI 0.7598

learned vs observation_side:
  ARI 0.1432
  NMI 0.6363
```

Thus, the learned partition is not simply recovering a better
observation-side quotient. The hidden quotient is valid in teacher parameter
space, but the current passive likelihood route does not isolate it from
detector/logical observations.

### DISC13b Inverse-Logit Recovery Gap

DISC13b is a short bridge audit before active probes.

It asks:

```text
Is the bottleneck failure to estimate oracle-like per-fault logits, or does the
assignment learner fail even when oracle-like logit structure is present?
```

DISC13b compares fitted local per-fault logits against oracle teacher logits:

```text
corr(local_logit_j, oracle_logit_j)
R2(local_logit -> oracle_logit)
rank / singular spectrum of oracle-logit matrix
rank / singular spectrum of fitted-local-logit matrix
ARI(cluster(local_logit), omega)
ARI(cluster(oracle_logit), omega)
ARI(cluster(local_logit), cluster(oracle_logit))
```

Run:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.static.inverse_logit_audit \
  --config configs/scope_static/d3_r1_STAGE2A2_DISC13b_inverse_logit.yaml
```

Outputs:

```text
outputs/scope_static/STAGE2A2_DISC13b_inverse_logit/metrics.json
outputs/scope_static/STAGE2A2_DISC13b_inverse_logit/disc13b_summary.md
outputs/scope_static/STAGE2A2_DISC13b_inverse_logit/logit_clusters.json
outputs/scope_static/STAGE2A2_DISC13b_inverse_logit/oracle_logits.npy
outputs/scope_static/STAGE2A2_DISC13b_inverse_logit/local_logits.npy
```

Current result:

```text
local_logits_contain_partial_target_signal
```

Key evidence:

```text
oracle logits:
  ARI 1.0000
  NMI 1.0000

local logits:
  ARI 0.5187
  NMI 0.8287

corr(local, oracle): 0.9277
R2(local -> oracle): 0.9270
ARI(local cluster, oracle cluster): 0.5187
NMI(local cluster, oracle cluster): 0.8287
```

This narrows the failure mode. Per-fault local inversion contains substantial
target signal, but it still does not recover the hidden quotient strongly, and
the shared-assignment likelihood learner remains below this local-logit
clustering level. The next credible change is active observability design, not
more entropy, balance, separation, or passive contrast sweeps.

### Stage 2A Closure

Close the original direct quotient-recovery line as:

```text
Direct shared-assignment likelihood learning does not recover hidden omega,
even though local inverse logits contain substantial target signal.
```

This is stronger than the earlier closure because DISC13b shows that the
failure is not simply absence of quotient signal in all inverse quantities.
The signal is present in fitted local per-fault logits, but direct `S`/`alpha`
likelihood learning does not extract it.

## Stage 2C: Local Inverse Representation Discovery

Stage 2C promotes local inverse representations to first-class discovery
objects.

Question:

```text
Can we denoise, factorize, and cluster fitted local inverse representations
better than direct S/alpha learning?
```

The first Stage 2C experiment is:

```text
DISC15_local_logit_to_mechanism_discovery
```

Inputs:

```text
local logits or local response fingerprints
```

Methods:

```text
PCA / spectral denoising
graph smoothing over the visible DEM fault graph
sparse dictionary or NMF-style factorization
mixture clustering
overlapping mechanism codes
```

Primary baseline:

```text
local-logit clustering:
  ARI 0.5187
  NMI 0.8287
```

Any new method must beat this baseline, not merely beat DISC12.

Run:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.static.local_mechanism_discovery \
  --config configs/scope_static/d3_r1_STAGE2C_DISC15_local_logit_mechanism.yaml
```

Outputs:

```text
outputs/scope_static/STAGE2C_DISC15_local_logit_mechanism/metrics.json
outputs/scope_static/STAGE2C_DISC15_local_logit_mechanism/disc15_summary.md
outputs/scope_static/STAGE2C_DISC15_local_logit_mechanism/run_selection_audit.json
outputs/scope_static/STAGE2C_DISC15_local_logit_mechanism/representations/*.npy
outputs/scope_static/STAGE2C_DISC15_local_logit_mechanism/clusters/*_clusters.json
```

Evaluation:

```text
ARI/NMI vs omega, evaluator-only
cluster masses
split/merge audit
stability across seeds
no omega for training, initialization, checkpointing, or selection
```

Success criterion:

```text
beats local-logit baseline:
  ARI > 0.5187
  NMI > 0.8287

strong:
  ARI >= 0.80
  NMI >= 0.80
```

If DISC15 beats the local-logit baseline under observable-only selection, the
new path is:

```text
local inverse first, mechanism discovery second
```

If DISC15 cannot beat local logits, the next required change is active
observability.

Current result:

```text
evaluator_only_candidate_beats_baseline_no_observable_selection_claim
```

Key evidence:

```text
declared local-logit baseline:
  ARI 0.5187
  NMI 0.8287

measured train-env local-logit baseline:
  ARI 0.5739
  NMI 0.8618

observable-selected candidate:
  single_env_local_logit_env0
  ARI 0.3213
  NMI 0.7125

evaluator-best candidate:
  local_logit_probability
  ARI 0.7923
  NMI 0.9245
```

Interpretation:

```text
Local inverse representations are now a promising route: a visible
logit-plus-probability representation beats the local-logit baseline and nearly
reaches the strong recovery ARI threshold. However, this is not yet a deployable
Stage 2C success because the observable-only selection score did not choose it.
```

### DISC15c Confirmatory Local-Logit Probability

DISC15c returns to the synthetic oracle-recovery question, but with the stronger
Stage 2C representation.

Question:

```text
If local_logit_probability is predeclared, does it recover synthetic omega
without evaluator-based candidate selection?
```

Rules:

```text
predeclared representation: local_logit_probability
candidate selection: disabled
ARI/NMI: evaluator-only
hidden omega used for training: false
hidden omega used for selection: false
hidden omega used for final evaluation: true
```

Run:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.static.disc15c_confirmatory \
  --config configs/scope_static/d3_r1_STAGE2C_DISC15c_confirmatory.yaml
```

Outputs:

```text
outputs/scope_static/STAGE2C_DISC15c_confirmatory_local_logit_probability/metrics.json
outputs/scope_static/STAGE2C_DISC15c_confirmatory_local_logit_probability/disc15c_summary.md
outputs/scope_static/STAGE2C_DISC15c_confirmatory_local_logit_probability/clusters.json
outputs/scope_static/STAGE2C_DISC15c_confirmatory_local_logit_probability/local_logits.npy
outputs/scope_static/STAGE2C_DISC15c_confirmatory_local_logit_probability/local_logit_probability.npy
```

Current result:

```text
near_strong_confirmed

local_logit baseline:
  ARI 0.5739
  NMI 0.8618

predeclared local_logit_probability:
  ARI 0.7923
  NMI 0.9245
```

Interpretation:

```text
The Stage 2C representation result survives confirmatory testing without
candidate selection. It is near-strong but misses the strong ARI threshold by a
small margin. The next synthetic step is DISC16 active local-inverse
observability, not a return to direct S/alpha hardening.
```

## Stage 2D: Active Local-Logit Observability

Active probing should target local-logit separability, not only detector-rate
contrast.

Old DISC12b mainly asked:

```text
Can increasing between-environment observable contrast recover omega?
```

The Stage 2D question is:

```text
Which probes improve recoverability of local inverse logits?
```

### S2D Physical-Oracle Current Note

S2D_PHYS keeps repetition-style catalog-validation circuits and runs:

```text
PHYS0 preflight -> PHYS1 teacher -> PHYS2 oracle separability -> PHYS3 learner
```

S2D.4 showed balanced evidence is needed before overreading ARI on singleton
mechanism classes. S2D.5 diagnosed the current learner-limited failures as
RZZ-family mixing plus readout splitting; RX/RZ, readout/damping, and
Pauli/depolarizing/custom-Kraus groups were distinguishable in the audited
failed rungs. Response NLL is not yet trusted as a primary ranking signal when
the oracle-fingerprint predictor is worse than the global-mean predictor.

S2D.6 tested representation-only v3 on balanced setB/setC. It preserved the
setA regression and improved setC ARI, but did not reduce RZZ-family
merge/split counts. The next step is therefore active observability, not another
clustering-only representation.

Current catalog-validation step:

```text
S2D.7_RZZ_active_probe_design
```

S2D.7 exposed only learner-visible mixed-basis edge moments computed from shot
bits, probe-basis metadata, and visible edge schedule. Exact PTM/RZZ-Type
features remained PHYS2 audit-only upper bounds. Freeze label:

```text
S2D.7 = negative_static_mixed_basis_probe_result
```

It ruled out the hypothesis that the RZZ-family gap can be solved by static
mixed-basis edge moments computed from final shot bits. On balanced setB/setC,
real active edge moments matched the scrambled-basis control, so the intended
edge-product physics did not carry the missing mechanism signal. This does not
rule out active observability in general; it says the next probes must change
RZZ dynamics.

S2D.8a started with the cheapest dynamical probe, RZZ depth sweep:

```text
S2D.8a_RZZ_depth_sweep
```

It kept setA clean and improved some global balanced scores, but depth features
matched the scrambled-depth control and did not close the RZZ-family merge/split
gap. Phase label:

```text
S2D.8a = depth_sweep_control_matched_negative
```

Next catalog-validation step:

```text
S2D.8b_RZZ_echo_no_echo_probe_design
```

S2D.8b is implemented as paired learner-visible echo/no-echo contrasts, not
raw echo moments. It uses colored even/odd RZZ-edge probes so left/right echo
roles are reproducible on a chain, compares against a scrambled-echo control,
and keeps exact PTM/RZZ-Type/oracle fingerprints PHYS2 audit-only. The full
GPU run kept setA clean, failed balanced setB, and gave only a control-limited
partial improvement on balanced setC: real echo did not beat scrambled echo.
Phase label:

```text
S2D.8b = echo_no_echo_mixed_control_limited
```

Artifacts live under
`outputs/scope_static/S2D.8_RZZ_dynamical_probe_design/S2D.8b_RZZ_echo_no_echo_probe_design/`;
the next active-probe step, if continued, is minimal twirl-style RZZ probes.

### S2D.8c_RZZ_observability_ceiling_audit

Status: planned / implemented boundary, results pending.

S2D.8c is an audit-only observability ceiling inserted before twirl-style
probes. It asks whether the existing S2D.8b balanced artifacts already contain
transferable RZZ-family signal in PHYS3-visible features. The primary audit
reuses the existing S2D.8b artifact tree and performs no new teacher sampling.

Primary rows are RZZ-family rows only: M1 / M6 / M7 / M9. Primary runs are
balanced setB and balanced setC; setA is regression/context only and is not
included in the primary verdict.

Primary model:

```text
StandardScaler + LogisticRegression(class_weight="balanced")
```

Primary validation:

```text
Leave-one-circuit-id-out grouped validation
```

Primary PASS/FAIL feature block:

```text
v3c_plus_active_all
```

Key explanatory blocks:

```text
active_residualized_against_v3c
scrambled_active_residualized_against_v3c
```

Oracle mechanism labels may be used only as supervised targets and diagnostic
metadata in this audit. They are forbidden as PHYS3 learner features,
clustering inputs, or oracle fingerprints. Store separate schemas for
PHYS3-visible features and oracle-only audit labels.

Controls:

```text
scrambled-active control
permutation-label control
```

Full run-level success requires:

```text
macro F1 >= 0.80
balanced accuracy >= 0.80
real_minus_scrambled_balanced_accuracy >= 0.25
real_minus_permutation_balanced_accuracy >= 0.25
all major pairwise margins > 0
no single class recall < 0.65
```

Global success requires both balanced setB and balanced setC to pass. If one
passes and one fails, the verdict is mixed_condition_specific_signal.

Interpretation:

```text
If the primary linear ceiling succeeds:
  existing PHYS3-visible stack contains transferable RZZ-family signal;
  the bottleneck is clustering / representation geometry.

If the linear ceiling fails but nonlinear diagnostics succeed:
  signal may exist but is not linearly/geometrically exposed.

If both fail:
  current feature blocks likely do not expose robust RZZ-family signal;
  this motivates S2D.8d twirl/tomography-like probes.
```

Pre-run result placeholder:

```text
Pending S2D.8c run. Append:
- setB verdict
- setC verdict
- conservative global verdict
- primary metrics table
- control table
- residualized-active attribution summary
- decision for S2D.8d
```

S2D.8c result:

```text
S2D.8c verdict:
  setB: FAIL
  setC: FAIL
  global: GLOBAL_FAILURE
```

Primary linear ceiling, `v3c_plus_active_all`:

```text
phys9_multicircuit_setB_balanced:
  macro F1 = 0.2500
  balanced accuracy = 0.2222
  real - scrambled balanced accuracy = -0.2222
  real - permutation balanced accuracy = -0.0217
  min class recall = 0.0000

phys9_multicircuit_setC_balanced:
  macro F1 = 0.5278
  balanced accuracy = 0.5833
  real - scrambled balanced accuracy = -0.0833
  real - permutation balanced accuracy = 0.4017
  min class recall = 0.0000
```

Leakage guardrails passed: oracle labels, mechanism ids, exact PTM columns,
teacher-channel columns, and oracle-fingerprint columns were absent from feature
columns; grouped validation used circuit_id transfer splits. Residualized active
features did not beat scrambled residualized controls on balanced setB or setC.
Secondary nonlinear diagnostics did not produce a strong rescue signal.

S2D.8c therefore supports the probe-limited interpretation: the existing saved
S2D.8b final-shot feature stack does not contain robust transferable
learner-visible RZZ-family signal under the balanced regimes. The next
scientific probe step is S2D.8d minimal twirl-style / tomography-like RZZ
interventions, not larger circuits, setD, or more final-shot feature dressing.

### S2D.8d_RZZ_minimal_intervention_probe

Status: implemented, results pending.

Purpose: S2D.8d adds minimal learner-visible interventions around RZZ-adjacent
regions to test whether M8/M9/M10/M12 become observably different when the probe
changes Pauli frame, basis response, or sign-flip/echo sensitivity. PHYS3
features remain restricted to shot bits, probe metadata, visible edge schedule,
and location metadata; exact PTM/RZZ-Type features, teacher channels, oracle
fingerprints, and oracle labels remain audit-only.

Probe families:

```text
baseline:
  no intervention

pauli_frame_twirl:
  deterministic local Pauli-frame representatives on even/odd RZZ edges

basis_rotation:
  X/Y/XZ/YZ readout-basis interventions

sign_flip_echo:
  no-flip and left/right sign-flip echo representatives on even/odd RZZ edges
```

Primary runs remain `phys9_setA`, `phys9_multicircuit_setB_balanced`, and
`phys9_multicircuit_setC_balanced`. The output bundle is:

```text
outputs/scope_static/S2D.8_RZZ_dynamical_probe_design/S2D.8d_RZZ_minimal_intervention_probe/
```

Required artifacts include `intervention_schema.json`,
`mechanism_response_table.json`, `twirl_response_metrics.json`,
`basis_response_metrics.json`, `echo_response_metrics.json`, grouped-fold
ceiling outputs, controls, leakage guardrails, and residualized-active
attribution. Full success requires global ARI/NMI recovery, improved
RZZ-family merge/split metrics, real intervention features beating scrambled
controls, and grouped transferable ceiling evidence.

S2D.8d result:

```text
S2D.8d = minimal_intervention_negative

phys9_setA:
  regression pass

phys9_multicircuit_setB_balanced:
  baseline v3c:              0.9361 / 0.8284
  minimal intervention all:  0.9136 / 0.7529
  scrambled intervention:    0.9136 / 0.7529
  grouped ceiling:           FAIL
  RZZ error base/all:        3 / 4

phys9_multicircuit_setC_balanced:
  baseline v3c:              0.9177 / 0.7914
  minimal intervention all:  0.9029 / 0.7739
  scrambled intervention:    0.9029 / 0.7739
  grouped ceiling:           FAIL
  RZZ error base/all:        3 / 5
```

The decisive control is that real minimal-intervention features match the
scrambled intervention control on both balanced primary runs. The grouped
ceiling audit also fails because macro F1 / balanced accuracy remain below the
success thresholds and real-minus-scrambled balanced accuracy is 0. S2D.8d
therefore rules out this minimal deterministic intervention set as sufficient
for RZZ-family mechanism recovery. The next justified probe step is stronger
benchmarking/tomography-like local channel characterization, not larger circuits
or more passive/static feature dressing.

Do not move to larger circuits, setD, Google transfer, S3, or a robustness grid
before deciding whether to implement stronger benchmarking/tomography-like
local RZZ channel probes.

### S2D.9_local_Pauli_Lindblad_observability

Status: implemented.

S2D.9 pivots the RXX/RZZ/RYY recovery issue from multiclass response-feature
clustering to local generator-coordinate identifiability. The primary object is
the learner-visible local response Jacobian, not classifier performance.

The implemented probe set is `rzz_local_tomography`: local two-qubit process
tomography on even/odd adjacent RZZ-edge batches using `Zp/Zm/Xp/Yp`
preparations and `X/Y/Z` measurements. The PTM convention is explicit:

```text
R[row_out, col_in] = Tr(P_out E(P_in)) / d
v_out = R v_in
post-ideal error: R_error = R_est @ pinv(R_ideal)
official v1 generator target: R_error - I
```

Hard sign tests lock the convention:

```text
ideal RZZ + small RXX -> recovered h_XX dominant with correct sign
ideal RZZ + small RZZ -> recovered h_ZZ dominant with correct sign
RXX/RYY mixture -> recovered h_XX and h_YY with correct relative magnitude
```

S2D.9 result:

```text
S2D.9 = local_generator_observability_partial

phys9_setA:
  regression pass
  response Jacobian rank: 10 / 10

phys9_multicircuit_setB_balanced:
  decision: partial_identifiable
  response Jacobian rank: 10 / 10
  grouped generator-coordinate ceiling: FAIL

phys9_multicircuit_setC_balanced:
  decision: partial_identifiable
  response Jacobian rank: 10 / 10
  grouped generator-coordinate ceiling: PASS
```

Interpretation: the local Pauli-Lindblad generator dictionary is identifiable
under the S2D.9 tomography design, so the previous RZZ-family failures were not
an unavoidable rank/observability impossibility. However, recovery/signature
evidence is incomplete: setC passes the grouped secondary ceiling, while setB
does not, and the simple mechanism-signature rules are still dominated by
normalization/non-unital nuisance for some classes. The next step should debug
coordinate normalization, nuisance residualization, and generator-space decision
geometry before adding larger circuits or more mechanisms.

### S2D.10_generator_space_calibration_and_nuisance_geometry

Status: implemented; result appended after run.

Purpose: S2D.10 does not add probes. It reuses the full-rank S2D.9 generator
coordinates and asks why balanced setB fails while balanced setC passes. The
primary object is generator-space calibration: effective rank, per-generator
signal-to-noise, nuisance residualization, and decision geometry.

Diagnostics:

```text
effective rank:
  singular values, condition number, stable rank, sigma_min, column angles

per-generator statistics:
  mechanism means/stds, between/within ratio, circuit/edge residual variance,
  shot-noise proxy

nuisance geometry:
  raw, edge-residualized, circuit-residualized, edge+circuit residualized,
  ideal-schedule residualized coordinates

decision geometry:
  blockwise Hamiltonian/stochastic/affine routing
  Mahalanobis nearest generator prototype
  z-score / whitening / circuit-residualized grouped ceiling
```

PHYS3-visible inputs remain the recovered S2D.9 generator coordinates computed
from shot-derived local tomography. Oracle labels are evaluator-side targets
only. No exact PTM, teacher channel, oracle fingerprint, or mechanism id is used
as a feature. The audit keeps RZZ-family decision metrics restricted to
M8/M9/M10/M12 while broad coordinate statistics may summarize all mechanisms.

S2D.10 result:

```text
S2D.10 = generator_space_calibration_partial

phys9_setA:
  decision: failure as RZZ-family calibration context
  response Jacobian rank: 10
  condition number: 9.5824

phys9_multicircuit_setB_balanced:
  decision: failure
  circuit-residualized grouped ceiling: 0.7778 balanced accuracy
  confusion: M8/M9 cross-confusion; M10 recall 1.0
  real - scrambled balanced accuracy: 0.4444
  Mahalanobis prototype balanced accuracy: 0.7778
  stage1 block accuracy: 0.2222

phys9_multicircuit_setC_balanced:
  decision: partial_blockwise_or_geometry
  circuit-residualized grouped ceiling: 0.9167 balanced accuracy
  confusion: one M1 -> M6; M6/M7/M9 recall 1.0
  real - scrambled balanced accuracy: 0.5000
  Mahalanobis prototype balanced accuracy: 1.0000
  stage1 block accuracy: 0.5000
```

Interpretation: calibration confirms the S2D.9 split rather than fixing it.
SetC contains a transferable generator-space decision signal under grouped
folds and Mahalanobis geometry. SetB is close but still below the flat recovery
threshold. The weak point is not algebraic rank; it is nuisance geometry and
mechanism block dominance. After circuit residualization, M6 and M7 remain
affine/non-unital dominated in the simple block audit, so the current flat
coordinate geometry is not yet a clean Hamiltonian/stochastic/relaxation
separator for setB.

### S2D.10b_generator_invariant_calibration

Status: implemented.

S2D.10b tests the direct physics/math fix suggested by S2D.10: append
learner-visible scalar invariants to the S2D.9 generator-coordinate table,
without adding probes or resampling the teacher. The invariants are computed
from shot-reconstructed generator coordinates and local PTM estimates only.

Invariant block:

```text
coherence_norm
stochastic_l1 / stochastic_l2
generator_total
log_coherence_ratio
coherence_ratio_capped
gamma_mean / gamma_variance / gamma_isotropy_score
h_xxyy_norm
h_zz_axial_ratio
h_zz_fraction
affine_nonunital_norm
nonunital_to_total
unitarity_R_error / unitarity_loss_R_error
unitarity_R_est / unitarity_loss_R_est
```

S2D.10b result:

```text
S2D.10b = generator_invariant_calibration_positive

phys9_multicircuit_setB_balanced:
  decision: success
  circuit-residualized generator+invariants balanced accuracy: 0.8889
  macro F1: 0.8857
  min recall: 0.6667
  real - scrambled balanced accuracy: 0.5556
  M8/M9 pairwise accuracy: 0.8333
  Mahalanobis prototype balanced accuracy: 1.0000

phys9_multicircuit_setC_balanced:
  decision: success
  circuit-residualized generator+invariants balanced accuracy: 1.0000
  macro F1: 1.0000
  min recall: 1.0000
  real - scrambled balanced accuracy: 0.5000
  M8/M9 pairwise accuracy: 1.0000
  Mahalanobis prototype balanced accuracy: 1.0000
```

Interpretation: the setB/setC gap was not a missing-probe problem after S2D.9.
The S2D.9 local channel estimate already contained the needed signal, but it
was poorly exposed in the raw coordinate geometry. Scalar invariants make the
coherent-vs-stochastic and ZZ-vs-XX/YY structure explicit enough for grouped
recovery. In this run, `coherence_norm`, `log_coherence_ratio`, and
`h_zz_axial_ratio` carry the clearest setB M8/M9 signal; unitarity is retained
as a physical audit feature but is not the main separator for this artifact.

Next: promote the invariant block into the physical generator learner
representation and keep the leakage boundary:

```text
allowed:
  shot-reconstructed local PTM
  fitted generator coordinates
  scalar invariants computed from those estimates

forbidden:
  exact teacher channel
  exact teacher PTM
  oracle mechanism label as a feature
  oracle fingerprints
```

### S2D Physical Teacher CUDA-Q Policy

Status: implemented.

The physical teacher now preflights CUDA-Q directly and routes PHYC1 generation
through the literal full-circuit CUDA-Q teacher. The default CUDA-Q target
policy is:

```yaml
backend: cudaq
require_gpu: true
cudaq_target: nvidia
cudaq_target_options: fp32
physical_teacher_model: full_circuit_cudaq
```

PHYS0 writes `backend_audit.json` and `backend_audit.md` with the CUDA-Q package
versions, selected target, visible GPU count, and a tiny sampled CUDA-Q kernel.
The physical teacher requires that audit to pass before writing PHYS1 artifacts.
The compact pipeline summary records this under `cudaq_backend`.

The current Stage 2E PHYC1 mainline samples:

```text
rho_probe -> full n-qubit ideal schedule of configured depth d
-> mechanism channels/readout -> sampled observations
```

Configured and effective circuit depth must match for `full_circuit_cudaq`.
Entangling operations remain real circuit operations. Readout mechanisms may be
applied as readout assignment/postprocessing when that is the declared
mechanism model. The teacher refuses CPU fallback when `require_gpu: true`.

Floating numerical floors, probability leftovers, and simulation thresholds use
the repository-wide numerical floor `scope_static.numerics.NUMERICAL_ZERO =
1e-12` instead of exact `0.0`. This value is chosen to survive square/cube
operations in GPU float32. This requirement is intentionally limited to floating
numerical floors. Structural zeros remain exact where they carry meaning:
Pauli/operator matrix entries, bit values, integer indices, counts, labels,
array sizes, empty-artifact metrics, and exact algebraic identities.

Named chain profiles currently include `phys5_chain`, `phys7_chain`,
`phys9_chain`, `phys15_chain`, and `phys20_chain`.

The local-observable GPU and Born-local teachers remain diagnostics and
historical evidence paths. They are not the Stage 2E PHYC1 mainline.

inspired by https://github.com/muhos/QuaSARQ

### S2D Catalog Pipeline Contract

Status: implemented.

The PHYC1/PHYC2/PHYC3 path is exposed through the Catalog Pipeline
facade:

```text
scope_static.catalog_pipeline.run_catalog_pipeline
scope_static.experiments.qec_noise_catalog.catalog_pipeline
```

The pipeline keeps existing legacy stage artifacts where needed, but the claim
vocabulary is:

```text
PHYC1:
  physical teacher generation from the declared teacher contract

PHYC2:
  teacher self-distinguishment from teacher-internal mechanism evidence

PHYC3:
  no-leakage learner recovery plus quantum/readout error quality from
  learner-visible grouped predictions
```

PHYC2 is exposed through
`scope_static.experiments.qec_noise_catalog.teacher_distinguishment` as a
companion audit for PHYC1 teacher artifacts. The runner keeps its historical
name for compatibility, but the primary PHYC2 gate is teacher
self-distinguishment: a teacher passes only when it can separate every generated
mechanism with BA, min recall, ARI, and NMI all equal to `1.0`. PHYC2 does not
emit learner grouped predictions. If grouped predictions are produced from
learner-visible sampled observations, they belong to PHYC3 learner recovery.
Exact PTMs, exact channel fingerprints, teacher-self signatures, oracle
mechanism IDs, and oracle labels remain evaluator-only and cannot be learner
feature inputs.

PHYC2 has two support variants:

```text
PHYC2-balanced:
  Question: can the teacher self-distinguish every enabled mechanism?
  Use: teacher-identifiability gate.
  Support contract: equal record support per mechanism class.
  Primary PHYC2 metrics: teacher-self BA, min recall, ARI, NMI all equal 1.0.

PHYC2-weighted:
  Question: can the teacher self-distinguish every enabled mechanism under
            uneven mechanism support?
  Use: deployment-like checks after balanced teacher self-distinguishment.
  Support contract: unequal class support is allowed, but every evaluated class
                    must appear in at least two grouped folds.
  Primary PHYC2 metrics: teacher-self BA, min recall, ARI, NMI all equal 1.0.
```

The default PHYC2-balanced teacher-self requirements are:

```text
num_groups >= 2
each mechanism class appears in at least two circuit_id groups
equal class support
teacher-self balanced accuracy = 1.0
teacher-self min class recall = 1.0
teacher-self ARI = 1.0
teacher-self NMI = 1.0
```

The default PHYC2-weighted teacher-self requirements are:

```text
num_groups >= 2
each evaluated mechanism class appears in at least two circuit_id groups
teacher-self balanced accuracy = 1.0
teacher-self min class recall = 1.0
teacher-self ARI = 1.0
teacher-self NMI = 1.0
```

For balanced evidence, the class recall resolution is `1 / support_per_class`.
A six-batch balanced allM run has recall steps of `1/6 = 0.1667`, so it is a
useful smoke/stress artifact but still low support. Serious balanced
separability runs should increase per-mechanism support when memory permits.

Current PHYC2-balanced allM evidence uses the local-observable Torch CUDA
teacher with `local_observable_response_model: separability_v2` and
`balanced_min_instances_per_mechanism: 30`:

```text
outputs/scope_static/local_observable_gpu_allM_30q_depth30_30groups_v2_slot_remap/

30 qubits, depth 30, historical M0-M19, 30 groups, 10k shots:
  contract_passed = true
  balanced_accuracy = 1.0000
  min_class_recall = 1.0000
  real_minus_within_branch_scrambled_balanced_accuracy = 0.8567
  PHYC3_contract_passed = true
  PHYC3_mean_predicted_channel_distance = 0.000085
  PHYC3_max_predicted_channel_distance = 0.003292
```

`separability_v2` is a sampled-observation teacher response model, not a global
full-circuit simulator. It keeps PHYS1 artifact compatibility while making
branch-specific local responses learner-visible:

- readout mechanisms `M1/M2/M3/M16` receive directional and context response
  signatures;
- RZZ-family mechanisms `M8/M9/M10/M12` receive GPU-side pair-correlation
  overlays in addition to marginal bit responses;
- gate, prep, and reset mechanisms retain local axis/strength signatures plus a
  deterministic response-code margin emitted only through sampled observations.

The local-observable teacher records
`sampling.observation_slot_remap` in `summary.json` and `sampling_audit.json`.
This remap is expected: it assigns non-overlapping local observation slots within
each circuit batch so one mechanism's sampled response cannot overwrite another
mechanism's response at the same probe/qubit cell. The original physical qubits
are preserved in each mechanism record as `physical_qubits`; learner-visible
`qubits` are the local observation slots used by the sampled tensor. PHYC2
neutralizes synthetic slot-geometry features for these records while keeping
branch flags, probe metadata, sampled response projections, and pair-correlation
features learner-visible.

Each PHYS1 local-observable teacher artifact also writes
`self_distinguishability_preflight.json`, which reports expected-response
pairwise margins for readout aliases, RZZ aliases, and historically low-margin
mechanism pairs before running PHYC2.

PHYC3 learner recovery reports `PHYC3.slot_only_leakage_control` style leakage
controls. These grouped controls use only observation-slot metadata, original
`physical_qubits`, probe block ids, and layout/slot metadata. They exclude
sampled bits, sampled response statistics, pair correlations, local-inverse
features, exact PTMs, mechanism ids, and oracle labels. High slot-only balanced
accuracy means the remap/layout is encoding mechanism identity and the PHYC3
learner result should not be trusted.

The data-preparation teachers support PHYC2-weighted data generation through
catalog-resolved `mechanism_weight_profile` names or explicit
`mechanism_instance_counts`. Use `weighted_realistic_v1` for realistic-ish
superconducting-QEC exposure imbalance and `weighted_discovery_floor_v1` when
rare/high-impact mechanisms need a minimum support floor. These profiles are
not hardware-calibrated mechanism frequency distributions.

Historical PHYC2-weighted allM evidence:

```text
outputs/scope_static/local_observable_gpu_allM_30q_depth30_weighted_v2_slot_remap/

30 qubits, depth 30, historical M0-M19, uneven support 2-8, 10k shots:
  contract_passed = true
  balanced_accuracy = 1.0000
  min_class_recall = 1.0000
  prevalence_weighted_accuracy = 1.0000
  rare_class_recall_min = 1.0000
  real_minus_within_branch_scrambled_balanced_accuracy = 0.8779
  slot_only_leakage_control_balanced_accuracy = 0.0313
  slot_only_leakage_suspected = false
```

Learner has two linked jobs. First, learner recovery trains grouped
classifiers from learner-visible sampled observations and writes grouped
predictions. Second, sampled quantum-error quality consumes those learner
predictions, builds fold-trained mechanism channel/readout prototypes from
training groups, and compares the predicted prototype with the evaluator-only
oracle mechanism channel. It must reject teacher-self
predictions as learner evidence.

```text
PHYC2:
  Can the teacher self-distinguish every generated mechanism?

PHYC3 learner recovery:
  Can sampled observations classify the mechanism without hidden/oracle leakage?

PHYC3 error quality:
  If the no-leakage learner predicts a mechanism, does that prediction produce
  a close quantum/readout error object?
```

Current PHYC3 weighted allM evidence:

```text
outputs/scope_static/local_observable_gpu_allM_30q_depth30_weighted_v2_slot_remap/PHYC3_quantum_error_quality/

30 qubits, depth 30, historical M0-M19, uneven support 2-8, 10k shots:
  contract_passed = true
  mechanism_balanced_accuracy = 1.0000
  mechanism_min_class_recall = 1.0000
  mean_predicted_channel_distance = 0.000026
  max_predicted_channel_distance = 0.001364
  incompatible_predictions = 0
```

For `separability_v2`, Learner is a mechanism-to-error translation diagnostic,
not proof that sampled observations came from Born-rule circuit physics.

The public pre-release code responsibilities are:

```text
data_preparation: Data Preparation (Prep)
  legacy alias: PHYC1

teacher: Teacher Self-Distinguishment (Teacher)
  legacy alias: PHYC2

learner: Learner Classification and Noise Generation (Learner)
  legacy alias: PHYC3
```

Data preparation writes the mechanism records, probe schedules, observations, and
sampling audits. Teacher is teacher/catalog self-distinguishability only and
must not be cited as no-leakage learner evidence. Learner owns learner-visible
classification, channel/readout prototype quality, and visible noise-generation
NLL/MAE.

Z/X visible repair is the visible-observability repair stage for the full-circuit/CUDA-Q
learner bottleneck. It is not a classifier-tuning stage: it first asks whether
the learner-visible deterministic ceiling improves under new probes, then
reports learner recovery. The probe suite is strictly Y-free and uses only
Clifford Z/X preparation and measurement:

```text
single-qubit: prepare |0>, |1>, |+>; measure Z or X; repeat r in {1,2,4,8}
two-qubit:    prepare |00>, |01>, |10>, |++>; measure ZZ, ZX, XZ, XX
```

Y-basis preparation and Y-basis measurement are not required. X-prepared states
are required because Z-only probes do not expose the phase/coherence response
needed to break several visible aliases. Z/X visible repair reports quotient alias classes
instead of forcing exact labels whenever the Z/X sampled observations do not
make exact recovery observable.

The distributional learner head is the upgrade on top of Z/X visible repair. It keeps the same
Z/X-visible feature vectors and compares mean-only, covariance-only, diagonal
Gaussian, shared-covariance LDA, full Gaussian, and shrinkage-QDA heads. It
reports two modes:

```text
single-realization mode:
  pointwise mechanism appearance; M13 can collapse into a fixed coherent
  rotation such as M6, M20, or M27

multi-context batch mode:
  drifted-mechanism distribution recovery from several locations, time windows,
  calibration contexts, or generated drift samples
```

M13 should be expected to become perfectly recoverable only in multi-context
batch mode. The Gaussian calibration parameters are learned from training
groups only; test labels remain evaluator-only and are not learner-visible
features.

Distributional learner-head validation is an acceptance audit for the head, not another learner input
source. It reports a robustness grid over batch size, shrinkage, and PCA
dimension; an explicit non-leakage audit with forbidden-feature injection
control; and a protocol-validity audit that rejects single-realization M13
batches as invalid for distributional recovery claims.

Canonical learner quality acceptance is a resolver, not another learner. It
loads the teacher-self artifact, the old-surface learner
baseline, the Z/X visible-repair artifact, distributional learner-head
predictions, and distributional learner-head validation. It accepts learner
validation only when Z/X visible repair has deterministic visible ceiling 1.0
and the distributional learner head passes the multi-context distributional protocol. The canonical
prediction source is `phyc3c_distributional_gaussian_likelihood_head`; PHYC2
teacher-self predictions, legacy PHYC2 grouped predictions, and PHYC3a
old-surface predictions are rejected as canonical learner evidence.

Stage 2 is closed as a no-leakage physical-mechanism catalog validation stage:
the system can generate controlled noisy QEC observations from declared
mechanisms, verify teacher/catalog separability, and train learner models
that recover and replay learner-visible noisy observation distributions without
oracle leakage. Stage 3 is the next claim boundary: remove direct
mechanism-label supervision and test whether latent mechanism structure can be
inferred from visible observations alone.

Current slot-only and no-remap guardrail evidence:

```text
PHYC2-balanced slot-only BA:
  0.0000

PHYC2-weighted slot-only BA:
  0.0313

PHYC2.no_slot_remap_ablation weighted BA:
  0.9708

PHYC2.weighted slot-remap weighted BA:
  1.0000
```

Current 74-qubit depth-200 weighted scalability smoke:

```text
outputs/scope_static/local_observable_gpu_allM_74q_depth200_weighted_v2_slot_remap/

30q -> 74q extension, depth 30 -> 200, same weighted allM support 2-8:
  contract_passed = true
  balanced_accuracy = 1.0000
  min_class_recall = 1.0000
  prevalence_weighted_accuracy = 1.0000
  rare_class_recall_min = 1.0000
  slot_only_leakage_control_balanced_accuracy = 0.0479
  slot_only_leakage_suspected = false
  teacher_total_requested_bits = 1,704,960,000
  teacher_total_wall_clock_seconds = 4.0741
  artifact_size = 1.7G
```

The same PHYC3 quantum-error-quality audit passes on the 74-qubit/depth-200
weighted artifact with the same classification and channel-distance metrics.

Stage 2E replaces the engineered `separability_v2` response model with a
literal full-circuit CUDA-Q teacher:

```text
rho_probe -> full n-qubit ideal schedule of configured depth d
-> mechanism channels/readout -> sampled observations
```

Configured and effective circuit depth must match for this teacher. The teacher
must not use mechanism-label response templates, artificial response-code
margins, local-observable shortcuts, or post-sampling pair-correlation overlays.
Small full-circuit CUDA-Q cases should be validated before using PHYC2/PHYC3 as
physical baseline evidence.

Use the names precisely:

```text
PHYC2-separability_v2:
  engineered separability stress teacher

PHYC2-Born-local:
  exact local Born-rule diagnostic, effective depth one

PHYC2-full-circuit-cudaq:
  required Stage 2E teacher self-distinguishment gate

PHYC3-full-circuit-cudaq:
  required Stage 2E no-leakage learner recovery and error-quality gate
```

Full-circuit CUDA-Q remains an important data preparation source for future larger-scale
physical-teacher runs. The current pre-release boundary is that Stage 2 is
closed as a controlled-catalog/no-leakage recovery validation stage, and Stage 3
now removes direct mechanism-label supervision to test latent mechanism
structure recovery from the same learner-visible observation surface.

The Born-local S2E.1 learner test is artifact-backed: it should consume an
existing PHYC3 learner-recovery `metrics.json` plus the linked PHYC1 teacher
metadata and write a separate S2E.1 report. Existing `separability_v2` learner
outputs can be used as negative controls, but they do not satisfy the
full-circuit source gate.

The legacy PHYS2 oracle-fingerprint audit remains useful as a ceiling: it says
whether the mechanism family is in principle distinguishable. It does not prove
that sampled observations are learner-separable.

The pipeline writes `catalog_pipeline.json` and
`catalog_pipeline.md` next to the canonical stage directories. Its verdicts
are intentionally separated: `teacher_self_verdict` answers whether the teacher
contains enough oracle mechanism signal, `learner_recovery_verdict` reports the
PHYS3 local-inverse result, and `overall_diagnosis` distinguishes
`probe_limited`, `strong_recovery`, `near_strong`, and `learner_limited`.

Under `run_local_inverse: auto`, PHYS3 is skipped when PHYS2 has
`ari < 0.85` or `nmi < 0.85`; diagnostic runners can request
`run_local_inverse: always`. The facade runs PHYS1 before importing the
Torch-heavy PHYS2/PHYS3 implementations, keeping backend visibility failures
localized to the PHYS0/PHYS1 boundary.

### Canonical S2D Physical Mechanism Taxonomy

Status: implemented for new S2D catalog-validation runs. The canonical source is
`src/scope_static/primitives/mechanism_catalog.py`; the cited taxonomy and legacy
renumbering table live in `docs/error_mechanisms.md`.

Named mechanism sets:

```text
set_A: M0-M9
set_B: M0-M14
set_C: M0-M24
set_D: M0-M34
allM:  M0-M34
```

Historical M0-M19 artifacts produced before the M0-M34 migration retain their
old labels and should be treated as pre-taxonomy-migration results.

### S2D.11_typed_gate_readout_prep_invariant_learner

Status: implemented; first efficiency-tuned set_D run complete.

Primary object:

```text
typed_gate_readout_prep_invariant_learner
```

This is a learner-visible typed representation and grouped supervised ceiling,
not a transformer and not a new probe experiment. It tests whether the existing
`rzz_local_tomography` observations can support the full set_D taxonomy once
gate/process, readout, and prep/reset rows are separated by visible instruction
type.

S2D.11 promotes the S2D.10b scalar invariant fix into the learner while
splitting non-gate mechanisms into explicit typed branches. The historical
short name `S2D.11_typed_SPAM_gate_invariant_learner` is retained for artifact
compatibility, but SPAM is implemented as two concrete branches:
`readout_branch` for visible `measure` rows and `prep_reset_branch` for visible
`reset` rows.

Primary scope:

```text
profile: phys9_multicircuit_setD_balanced
mechanism set: set_D = M0-M18
probe set: existing rzz_local_tomography
new probes: none
primary validation: grouped folds by circuit_id
secondary M19 stress: only after primary set_D pass
```

Learner-visible inputs remain:

```text
shot bits
probe prep/measurement metadata
visible instruction type
visible qubit ids / edge ids / chain position
shot-reconstructed local PTM/generator estimates
scalar invariants computed from those estimates
readout/prep summaries computed from observed shots
```

Current branch feature object:

```text
gate_process_branch:
  S2D.10b two-qubit generator invariants
  raw generator coordinates as ablation
  compact one-qubit/basis-response summaries
  visible instruction metadata
  visible location / chain-position metadata

readout_branch:
  readout response shape
  readout strength
  assignment-asymmetry proxy
  readout entropy / variance
  x-z and y-z readout contrasts

prep_reset_branch:
  prep_fidelity_proxy
  prep_axis_bias_x/y/z
  initial_state_affine_shift
  reset_prep_asymmetry
  prep confidence / SNR proxy
```

Feature confidence fields are attached to branch feature tables:

```text
feature_confidence
feature_snr
fit_residual_or_reconstruction_error
low_confidence_flag
```

Efficiency rule:

```text
Do not feed the dense full local-inverse/probe stack into the primary typed
learner. It is high-dimensional, slow, and can dilute the calibrated S2D.10b
gate signal. Use compact learner-visible basis-response summaries instead.
```

Forbidden as PHYS3 features:

```text
oracle labels
mechanism_id
exact teacher channel
exact teacher PTM
oracle fingerprints
final evaluator labels during feature construction
```

Branching:

```text
measure -> readout_branch
reset -> prep_reset_branch
otherwise -> gate_process_branch
```

Branch budgets are audit-only and come from the visible suite configuration,
not row-level labels. The artifacts write separate
`typed_branch_feature_schema_physics_visible.json` and
`audit_labels_schema_oracle_only.json`, plus branch-budget, grouped-coverage,
readout-mechanism, prep/reset readout-confound, typed-head, scrambled-control,
and oracle-upper-bound audits. Historical artifact aliases with `m5_`, `m11_`,
`m13_`, and `m1_` prefixes are retained for compatibility; current canonical
labels are readout `M1/M2/M3/M16`, prep/reset `M17-M18`, and other `M19`.

Current metric heads:

```text
typed_linear_head:
  TorchStandardScaler + DualRidgeLinearClassifier(class_weight=balanced)
  GPU-friendly fold-local dual solve
  replaces iterative sklearn logistic on high-dimensional tiny-fold data

typed_prototype_head:
  TorchNearestPrototype

typed_mahalanobis_prototype_head:
  TorchDiagonalShrinkageMahalanobisPrototype
  no dense d x d covariance inversion
```

The primary PASS/FAIL remains determined by the typed linear grouped ceiling.
Prototype and Mahalanobis heads remain required diagnostics, with the rule that
the Mahalanobis prototype head should not underperform the typed linear head.

Current set_D snapshot:

```text
run: phys9_multicircuit_setD_balanced
decision: failure_typed_branch_or_prep_design

typed primary linear head:
  balanced accuracy: 0.8689
  macro F1: 0.8614
  min recall: 0.3333
  real - within-branch scrambled balanced accuracy: 0.6638

Readout mechanisms:
  canonical labels: M1/M2/M3/M16
  historical M5 split audit alias retained

Prep/reset mechanisms:
  canonical labels: M17-M18
  prep/reset observability preflight: pass
  recall: 1.0000

low-recall class:
  M8 recall: 0.3333

typed_mahalanobis_prototype_head:
  balanced accuracy: 0.8462
  under typed linear head, so strict criterion fails
```

Interpretation: the typed branch object is now close to the set_D threshold and
clearly beats scrambled controls, but the strict S2D.11 primary pass is not
met. The remaining issue is narrow: readout and prep/reset branches are
functioning, while the gate branch still has an M8-specific grouped-fold weakness and the
diagonal-shrinkage Mahalanobis head slightly underperforms the typed linear
head. The next implementation work should inspect gate-branch feature
observability/calibration before adding probes.

### S2D.11b_M1_gate_branch_grouped_calibration_audit

Status: implemented; calibration-only pass.

S2D.11b reuses the existing S2D.11
`phys9_multicircuit_setD_balanced` artifact tree and performs no new teacher
sampling, no new probes, no transformer, no larger circuit, and no M19 stress.
It freezes the validated typed branches and changes only gate-branch M1
calibration.

Result:

```text
best variant: typed_linear_plus_M1_logit_boost
passed: true

baseline typed linear:
  balanced accuracy: 0.8689
  macro F1: 0.8614
  M8 recall (artifact M1 key): 0.3333

M8 logit boost (artifact M1 key):
  balanced accuracy: 0.8946
  macro F1: 0.8927
  M8 recall: 0.6667
  M10 RXX/RYY recall: 1.0000
  M12 correlated relaxation recall: 1.0000
  M17 prep/reset recall: 1.0000

top-level error type split:
  gate recall: 1.0000
  readout recall: 0.9630
  prep/reset recall: 1.0000
```

All S2D.11b acceptance checks pass:

```text
M8 recall >= 0.65
macro F1 >= 0.80
balanced accuracy >= 0.80
real - scrambled >= 0.25
readout split count stays within declared M1/M2/M3/M16 taxonomy
M10/M12/M17 recall drops <= 0.15 from S2D.11 baseline
M17/M4 and M17/M1 margins remain positive
leakage guardrails pass
```

Interpretation: S2D.11b converts the S2D.11 strong partial into a pass. The
remaining S2D.11 failure was gate-branch M1 calibration, not a readout/prep
branch failure and not a missing-probe result. In current M0-M34 labels this is
the M8 RZZ gate branch; the artifact name predates renumbering.

Primary verdict rules:

```text
typed learner must beat flat invariant/raw baselines and within-branch scrambled control
macro F1 >= 0.80
balanced accuracy >= 0.80
no primary class recall < 0.65
readout split count stays within the declared M1/M2/M3/M16 taxonomy
typed_mahalanobis_prototype_head must not underperform typed_linear_head
M17/M18 are required only if the prep-observability preflight is positive
```

Metrics:

```text
corr(local logits, oracle logits)
R2(local -> oracle)
ARI/NMI of clustered local logits
local-logit cluster margin
eigen-gap / singular spectrum of L[j,e]
heldout environment transfer
```

### DISC16a Shot-Budget Sweep

DISC16a tests the simplest active-observability explanation first:

```text
Can more local inverse evidence turn DISC15c ARI 0.7923 into ARI >= 0.80?
```

Rules:

```text
predeclared representation: local_logit_probability
candidate selection: disabled
ARI/NMI: evaluator-only
hidden omega used for training: false
hidden omega used for selection: false
hidden omega used for final evaluation: true
```

Run:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.static.disc16_observability \
  --config configs/scope_static/d3_r1_STAGE2C_DISC16a_shot_budget.yaml
```

Outputs:

```text
outputs/scope_static/STAGE2C_DISC16a_shot_budget/metrics.json
outputs/scope_static/STAGE2C_DISC16a_shot_budget/disc16a_summary.md
outputs/scope_static/STAGE2C_DISC16a_shot_budget/shot_sweep.json
outputs/scope_static/STAGE2C_DISC16a_shot_budget/cluster_audit.json
outputs/scope_static/STAGE2C_DISC16a_shot_budget/run_selection_audit.json
```

Current result:

```text
strong_recovery_by_predeclared_local_inverse_probability

shots   ARI  NMI  active  bootstrap NMI  prob variance
25k     1.0  1.0  9       1.0            0.003372
50k     1.0  1.0  9       1.0            0.001334
100k    1.0  1.0  9       1.0            0.0008979
200k    1.0  1.0  9       1.0            0.0005264
500k    1.0  1.0  9       1.0            0.0001955
```

Interpretation:

```text
DISC15c was just below strong recovery because the local inverse probability
estimator was noisy at the smaller evidence level. With 25k or more shots,
the predeclared local_logit_probability representation recovers the hidden
synthetic quotient exactly in this d3/r1 setting. Direct S/alpha likelihood
learning failed, but local inverse first plus probability representation
succeeds.
```

Protocol difference from DISC15c:

```text
DISC15c:
  local inverse source: DISC12 env_alpha artifact
  train environments: 0, 1, 2, 3
  shots per train environment: 2,048
  local inverse steps: 200
  representation: local_logit_probability
  clustering: deterministic k-means, K=9

DISC16a:
  local inverse source: freshly refit from synthetic observations
  train environments: 0, 1, 2, 3
  shots per train environment: 25k, 50k, 100k, 200k, 500k
  bootstrap replicates per budget: 2
  local inverse steps: 200
  representation: local_logit_probability
  clustering: deterministic k-means, K=9
```

Thus the intended causal change is the local inverse evidence budget, with
fresh sampling used to measure bootstrap stability.

Leakage audit:

```text
Allowed oracle use:
  synthetic teacher generation uses omega(j);
  final ARI/NMI and split/merge evaluation use omega(j);
  K=9 is used as known_K_synthetic_audit.

Post-sampling learner-visible path:
  observations + DEM parity map A
  -> local_full_per_fault_per_env inverse fit
  -> local_logit_probability = [lambda_hat, sigmoid(lambda_hat)]
  -> deterministic k-means with K=9

The post-sampling learner path does not read omega(j). A regression test
replaces graph.orbit_ids after observation sampling and verifies that the
local inverse logits, probability representation, and k-means labels are
unchanged. Only final evaluator metrics change with evaluator labels.
```

### DISC16b Local-Inverse Recovery Robustness

DISC16b checks whether the DISC16a recovery holds beyond one controlled
d3/r1 synthetic instance.

Grid:

```text
synthetic seeds: 0, 1, 2, 3, 4
shot budgets: 10k, 25k, 50k
regimes: easy, default, harder
representation: local_logit_probability
candidate selection: disabled
ARI/NMI: evaluator-only
K_mode: known_K_synthetic_audit
```

Run:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.static.disc16b_robustness \
  --config configs/scope_static/d3_r1_STAGE2C_DISC16b_robustness.yaml
```

Outputs:

```text
outputs/scope_static/STAGE2C_DISC16b_local_inverse_robustness/metrics.json
outputs/scope_static/STAGE2C_DISC16b_local_inverse_robustness/disc16b_summary.md
outputs/scope_static/STAGE2C_DISC16b_local_inverse_robustness/robustness_grid.json
outputs/scope_static/STAGE2C_DISC16b_local_inverse_robustness/failure_cases.json
outputs/scope_static/STAGE2C_DISC16b_local_inverse_robustness/run_selection_audit.json
```

Current result:

```text
robust_near_strong_some_hard_cases

regime   shots  seeds  ARImean  ARImin  NMImean  NMImin  active  strong
default  10000  5      0.8443   0.7426  0.9482   0.9136  9       3/5
default  25000  5      0.9360   0.7828  0.9798   0.9269  9       4/5
default  50000  5      1.0000   1.0000  1.0000   1.0000  9       5/5
easy     10000  5      0.8567   0.6742  0.9525   0.8885  9       3/5
easy     25000  5      0.9728   0.8611  0.9916   0.9581  9       5/5
easy     50000  5      0.9783   0.7828  0.9944   0.9443  9       4/5
harder   10000  5      0.8187   0.7320  0.9458   0.9123  9       2/5
harder   25000  5      0.9564   0.8295  0.9870   0.9515  9       5/5
harder   50000  5      0.9626   0.8673  0.9878   0.9581  9       5/5
```

Interpretation:

```text
DISC16a establishes strong recovery for one controlled d3/r1 instance.
DISC16b shows that local-inverse probability recovery is robustly near-strong
across seeds and regimes, with strong recovery in most 25k/50k conditions and
all default 50k conditions. It is not yet a universal all-seed/all-regime
perfect-recovery result because 10k conditions and a small number of 25k/50k
seed-regime cells fall below ARI 0.80.
```

Failure-case audit:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.static.stage2c_failure_audit \
  --metrics outputs/scope_static/STAGE2C_DISC16b_local_inverse_robustness/metrics.json
```

Outputs:

```text
outputs/scope_static/STAGE2C_DISC16b_local_inverse_robustness/failure_case_audit.json
outputs/scope_static/STAGE2C_DISC16b_local_inverse_robustness/failure_case_audit.md
```

Failure audit result:

```text
near_miss_ari_failures_no_cluster_collapse_mostly_low_shot_split_merge

strong conditions: 36/45
failure conditions: 9/45

failure reasons:
  ari_below_0.80: 9

failure counts by shots:
  10k: 7
  25k: 1
  50k: 1

failure counts by regime:
  easy: 3
  default: 3
  harder: 3

failure counts by seed:
  seed 1: 1
  seed 2: 1
  seed 3: 4
  seed 4: 3
```

Failure pattern:

```text
All failure cases keep active_clusters = 9.
All failure cases keep NMI >= 0.8885.
All failure cases fail only by ARI < 0.80.
Mean failure ARI_min: 0.7557.
Mean failure NMI_min: 0.9240.
Mean failure cluster purity: 0.9450.
Mean failure splits per omega: 1.148.
```

Interpretation:

```text
Stage 2C failures are near-miss split/merge errors, not model collapse.
The local-inverse probability representation usually recovers the hidden
synthetic quotient, but some seed/regime/evidence cells retain small split/merge
ambiguities that depress ARI while preserving high NMI and full cluster
activity.
```

Stage 2C freeze label:

```text
local_inverse_probability_robust_near_strong_with_near_miss_split_merge_failures
```

Frozen Stage 2C claim:

```text
Direct shared-assignment likelihood learning does not recover hidden omega.
Local-inverse-first discovery with the predeclared local_logit_probability
representation recovers the synthetic hidden quotient strongly in the controlled
DISC16a instance and robustly near-strong across the DISC16b seed/regime grid.
The remaining failures are near-miss ARI split/merge failures, concentrated
mostly at low evidence, not hidden-label leakage, assignment collapse, dead
prototypes, or NMI failure.
```

### DISC14 Active Probe Design

Active quotient discovery changes the synthetic data-generation setting instead
of only changing the optimizer.

Goal:

```text
Choose synthetic probe contexts that make local inverse representations more
separable and more oracle-like.
```

Possible probe axes:

- synthetic noise regimes.
- code family, basis, distance, or round count where global exact remains
  feasible.
- local-window families.
- detector/logical support windows.
- teacher prototype separation.
- controlled residual perturbations.

Possible selection criteria:

- prototype separation in learned or teacher logits.
- Fisher-information-like sensitivity.
- pair-correlation contrast.
- local-window likelihood curvature.
- KL or TVD contrast between candidate prototype perturbations.

This is a synthetic identifiability method. It does not imply the same probes
exist on Google data.

### DISC11 OT/Sinkhorn Assignment

OT/Sinkhorn discovery replaces independent row-softmax assignments with a
structured transport problem over the DEM fault graph.

Conceptual objective:

```text
min_S <S, C> + tau H(S) + lambda_graph Tr(S^T L_fault S)
subject to row and prototype-mass constraints
```

Where:

- `C[j,k]` is the cost of assigning fault `j` to prototype `k`.
- `H(S)` is entropy regularization.
- `L_fault` is a visible fault-graph Laplacian.
- prototype-mass constraints reduce collapse/dead prototypes.
- graph smoothness encourages similar visible faults to share prototypes.

This should be compared against:

```text
free_softmax
free_softmax + entropy/balance
hard or straight-through assignment
OT/Sinkhorn
OT/Sinkhorn + graph smoothness
```

Any OT assignment must still obey the no-hidden-`omega(j)` rule.

### DISC12 Multi-Environment Invariant Quotient

Multi-environment discovery assumes that quotient assignment is stable across
environments while prototype strengths vary:

```text
S^(e) approximately S*
alpha_k^(e) varies across environment e
```

Candidate environments:

- synthetic noise regimes.
- rounds.
- basis.
- patch location.
- calibration windows.
- sequential real experiments.

This is a bridge toward SCOPE-Twin and SCOPE-Dynamic, but it is not Stage 2A.0.
It should be used only after fixed-context synthetic recovery has been
understood. Invariance alone must not be treated as proof of latent quotient
recovery.

### Later Ideas Not In Stage 2A

The following ideas are useful but should not be the main Stage 2A path:

- decoder-in-the-loop quotient value: useful external utility test, but not a
  substitute for synthetic ARI/NMI recovery.
- hybrid DEM plus coherent/physical residual teachers: promising for later
  SCOPE-Twin work, but outside the fixed DEM/Bernoulli Stage 2A claim.
- full context-conditioned assignment networks: future amortized discovery,
  not evidence that fixed-context Stage 2A.0 recovered `omega(j)`.

## Stage 2B Google External Validation

Google datasets are useful for later external validation, not oracle discovery
or the first Stage 3 controlled-catalog discovery claim.

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

They do not provide the true hidden physical fault mechanism, true orbit
partition, or ground-truth physical mechanism labels needed for a Stage 3
discovery claim.

Use Google data to evaluate:

- heldout detector/logical likelihood.
- detector-rate matching.
- local-correlation matching.
- logical prediction.
- calibration and transfer.
- robustness across samples or time.
- external utility of discovered priors.

Do not use Google data to claim true latent partition recovery unless the
partition is explicitly defined as a proxy.

Run:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.google.static \
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

Google discovery records must report:

- no ground-truth hidden partition is available.
- ARI/NMI are unavailable unless using an explicit proxy partition.
- assignment entropy and active/dead prototype audits.
- free-assignment parameter accounting.
- heldout and transfer deltas against local and known-orbit-like baselines.

### Google DISC Tasks

The Stage 2B Google path separates three real-data questions.

```text
GDISC12_multi_context_shared_response:
  Question: Does shared response structure improve transfer across real
            contexts such as sample, patch, basis, cycles, time/window, or
            decoder pathway?
  Claim: predictive/context transfer only; no ARI.

GDISC13b_real_local_inverse_audit:
  Question: Do local inverse logits on Google data contain stable reusable
            structure, or mostly window-specific noise?

GDISC15_real_local_mechanism_discovery:
  Question: Can local inverse representations be clustered or factorized into
            useful real-data response modes?
```

Google DISC13b replaces synthetic oracle-logit metrics:

```text
synthetic corr(local, oracle)      -> stability across shot subsamples/windows
synthetic R2(local -> oracle)      -> predictiveness on heldout detector/logical data
synthetic ARI/NMI against omega    -> no true label; proxy ARI/NMI only if labelled
```

Google DISC15 may report proxy ARI/NMI only against explicitly labelled proxy
partitions:

```text
proxy_boundary_bulk
proxy_support_size
proxy_detector_degree
proxy_space_time_region
proxy_basis_type
proxy_round_layer
proxy_decoder_prior_family
proxy_fault_graph_community
```

These proxies answer:

```text
Do discovered real-data mechanisms align with interpretable geometry or
schedule structure?
```

They do not answer:

```text
Did we recover true physical mechanisms?
```

Smoke run:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.google.local_mechanism \
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

Outputs:

```text
outputs/google_static/GDISC13b_real_local_inverse_audit/metrics.json
outputs/google_static/GDISC13b_real_local_inverse_audit/summary.md
outputs/google_static/GDISC15_real_local_mechanism_discovery/metrics.json
outputs/google_static/GDISC15_real_local_mechanism_discovery/summary.md
outputs/google_static/STIM_vs_Google_comparison/summary.md
```

Current smoke result:

```text
GDISC15_smoke:
  early_positive_predictive_utility_under_parameter_compression
  continuous_local_inverse_stable
  discrete_cluster_identity_unstable
  proxy_labels_only_no_recovery_claim

GDISC13b:
  mean pairwise local-logit corr: 0.9177
  mean pairwise cluster NMI: 0.4310

GDISC15 selected:
  model: GDISC15_pca_scores_rank3
  parameters: 99
  heldout local-window excess NLL: 0.006583
  detector-rate MAE: 0.007060
  local-correlation error: 0.005075
  logical flip calibration: 0.002853

local_full baseline:
  parameters: 1341
  heldout local-window excess NLL: 0.006611
  detector-rate MAE: 0.007211
  local-correlation error: 0.005092
  logical flip calibration: 0.004470
```

Interpretation:

```text
The Google smoke suggests local inverse logits are stable at the logit level,
but their hard clusterings are less stable. A compressed PCA local-inverse
mechanism model slightly improves heldout excess NLL, detector-rate MAE,
local-correlation error, and logical calibration versus local_full while using
far fewer parameters. This is a predictive-utility result, not quotient or
physical-mechanism recovery.
```

### GDISC15b Google Grid Validation

GDISC15b scales the smoke to paired Google contexts and reports uncertainty:

```text
mean +/- std
paired improvement over local_full
number of contexts where the compressed model wins
```

Required baseline/model families:

```text
local_full
global_shared_scalar
SI1000 prior reference
RL-optimized prior reference, where available
GDISC15_pca_scores_rank{1,2,3,5,8}
random low-rank controls
```

Small grid run:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.google.gdisc15b_grid \
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

Outputs:

```text
outputs/google_static/GDISC15b_google_grid_validation/metrics.json
outputs/google_static/GDISC15b_google_grid_validation/flat_records.json
outputs/google_static/GDISC15b_google_grid_validation/run_manifest.json
outputs/google_static/GDISC15b_google_grid_validation/summary.md
```

Current small-grid result:

```text
contexts:
  samples: sample_00, sample_01
  patch: d3_at_q5_5
  basis: X, Z
  cycles: r13
  split: shot-heldout
  completed: 4

local_full:
  params: 1340.0 +/- 1.155
  heldout NLL: 0.7715 +/- 0.02805
  heldout excess NLL: 0.006607
  detector MAE: 0.007337 +/- 0.000450
  local corr err: 0.005122 +/- 0.000116
  logical calib: 0.01414 +/- 0.01213

GDISC15_local_logit:
  params: 98.5 +/- 0.577
  heldout NLL: 0.7715 +/- 0.02805
  heldout excess NLL delta vs local_full: +0.00000165
  wins/total: 0/4

GDISC15_pca_scores_rank3/5/8:
  params: 98.5 +/- 0.577
  heldout excess NLL delta vs local_full: +0.0000381
  detector MAE: 0.007285 +/- 0.000435
  wins/total: 1/4

random low-rank controls:
  worse than local inverse models on NLL, detector MAE, correlation, and
  logical calibration.

global_shared_scalar:
  worse than local inverse models and local_full.
```

Interpretation:

```text
The broader grid weakens the one-context smoke claim. Compressed local inverse
models preserve local_full heldout NLL surprisingly well under strong parameter
compression, but they do not yet win consistently. The current positive result
is compression-with-near-parity plus occasional small metric gains, not robust
predictive improvement.
```

## Decision Rules

Use this decision tree:

```text
If Stage 2A.0 has high ARI/NMI and low delta_nll_known_orbit:
  Record free-assignment synthetic recovery as successful.
  Proceed to Stage 2B external validation and optionally 2A.2.

If Stage 2A.0 has low delta_nll_known_orbit but poor ARI/NMI:
  Record likelihood-positive, recovery-negative.
  Run Stage 2A.1 hardening.

If Stage 2A.1 succeeds:
  Claim recovery only for the hardened regime, not for free-S 2A.0.
  Then consider Stage 2A.2 for stronger identifiability.

If Stage 2A.1 still fails:
  Treat the hidden quotient as weakly identifiable under passive observations.
  Prioritize Stage 2A.2 active/moment/OT/multi-environment tests.

If only Google improves:
  Claim external predictive value, not true hidden quotient recovery.
```

Negative results are scientifically meaningful. If discovery repeatedly matches
oracle likelihood but fails ARI/NMI under clean synthetic teachers, the honest
conclusion is that the fixed DEM/Bernoulli observations do not identify the
chosen hidden quotient under the tested learner and data regime.

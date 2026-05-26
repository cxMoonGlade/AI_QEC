# Stage 2 Roadmap: SCOPE-Static Discovery

This roadmap covers Stage 2 only.

Stage 2 keeps the fixed DEM/Bernoulli likelihood from Stage 1, but removes the
known orbit map from the learner. The core question is:

```text
Can observations identify hidden DEM-fault sharing structure?
```

Notation stays fixed:

```text
A          = DEM parity map
lambda_j   = DEM fault logit
omega(j)   = hidden teacher orbit/quotient label
S[j,k]     = learned assignment to discovery prototype k
K          = number of discovery prototypes
```

Stage 2 is split into six tracks:

```text
Stage 2A.0: Current free-assignment synthetic test
Stage 2A.0.5: Passive identifiability audit
Stage 2A.1: Proposed hardening study
Stage 2A.2: Proposed identifiability-aware discovery
Stage 2C:   Local inverse representation discovery
Stage 2D:   Active local-logit observability
Stage 2B:   Google external validation
```

Do not merge evidence across tracks. A stronger Stage 2A.1 or 2A.2 method does
not retroactively prove that the Stage 2A.0 free-assignment model recovered the
hidden quotient.

## Claim Boundary

Stage 2 may claim:

- synthetic hidden-quotient recovery when ground-truth `omega(j)` exists.
- heldout likelihood and calibration for learned discovery assignments.
- seed/shot/`K` robustness.
- real-data external predictive validation on Google data.

Stage 2 must not claim:

- CPTP/GKSL physical-channel learning.
- full noisy-circuit Born-rule likelihood.
- true latent quotient recovery from Google data.
- context-conditioned SCOPE-Twin discovery as part of Stage 2A.0.

## Three Different Objects

Stage 2 must keep three objects separate.

### Object 1: Predictive Latent Assignment

This is a learned assignment `S` that improves heldout likelihood,
calibration, transfer, or decoder-facing utility.

This object is enough for Stage 2B external value:

```text
external predictive validation of discovered DEM-fault sharing structure
```

It is not, by itself, evidence that the hidden synthetic quotient or a true
physical mechanism was recovered.

### Object 2: Synthetic Quotient Recovery

This is a learned assignment `S` whose hard labels:

```text
hat_omega(j) = argmax_k S[j,k]
```

match synthetic teacher `omega(j)` by ARI/NMI while also matching the
known-orbit oracle in heldout likelihood.

This is Stage 2A's main target.

### Object 3: True Physical Mechanism Discovery

This would mean the learned assignment corresponds to real device-level
physical fault mechanisms.

Stage 2 does not currently have labels or interventions sufficient to claim
this on Google data. Google Stage 2B should therefore be called:

```text
external predictive validation of discovered DEM-fault sharing structure
```

Do not call Google Stage 2B "quotient recovery" unless an explicit proxy
partition is defined and labelled as a proxy.

## Stage 2A.0: Free-Assignment Synthetic Test

Question:

```text
Can a free learned assignment S[j,k] recover hidden omega(j) from DEM
parity-map observations alone?
```

Model:

```text
S[j,k] = softmax(assignment_logits[j,:])_k
lambda_j = sum_k S[j,k] alpha_k
```

Soft residual extension:

```text
lambda_j = sum_k S[j,k] (alpha_k + beta_k^T phi_j)
```

Implemented models:

- `disc_hard`
- `disc_soft`
- `known_hard_orbit`
- `known_soft_feature_orbit`
- `local`
- `dmle_qec`

Core run:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_static_discovery \
  --config configs/scope_static/d3_r1_STAGE2A_full.yaml
```

Output:

```text
outputs/scope_static/STAGE2A_full/
```

Success requires both:

- high ARI/NMI against hidden `omega(j)`.
- heldout NLL close to the matched known-orbit oracle.

Default synthetic recovery threshold:
- ARI >= 0.80 and NMI >= 0.80 for strong recovery.
- ARI >= 0.60 or NMI >= 0.60 for partial recovery.
- delta_nll_known_orbit <= 5% of local-vs-oracle improvement gap.
- no prototype collapse: active prototype count >= K - 1 unless K sweep says otherwise.

Failure modes:

```text
good NLL + poor ARI/NMI = likelihood-positive, recovery-negative
good ARI/NMI + poor NLL = partition-like but poor predictive model
collapse/dead prototypes = invalid main-claim recovery run
```

Required metrics:

- ARI/NMI from `argmax_k S[j,k]`.
- assignment entropy mean and normalized entropy.
- prototype masses.
- active/dead prototype counts.
- collapse flags.
- `known_orbit_oracle_model`.
- `delta_nll_known_orbit`.
- `d_q_dem`.
- detector-rate MAE.
- local-correlation error.
- TVD when global exact is feasible.

Stage 2A.0 decision gate:

```text
If ARI/NMI are high and delta_nll_known_orbit is low:
  Free-assignment synthetic recovery passes.

If delta_nll_known_orbit is low but ARI/NMI are poor:
  Record likelihood-positive, recovery-negative.
  Move to Stage 2A.0.5.
```

## Stage 2A.0.5: Passive Identifiability Audit

Question:

```text
Before changing the optimizer, do passive visible signatures contain enough
information to separate hidden omega(j)?
```

This audit sits between the current free-assignment result and full hardening.
It is diagnostic, not a replacement for Stage 2A recovery.

The main experiment is DISC10.

### DISC10 Moment/Spectral Seed

Goal:

```text
Use visible fault signatures to initialize or diagnose quotient structure before
likelihood refinement.
```

Candidate signatures:

- detector-rate sensitivity.
- local pair-correlation signature.
- support size.
- boundary/bulk indicators.
- shared-detector profile.
- fault-graph neighborhood features.

Compare:

```text
random init
local-logit init
moment/spectral init
moment/spectral init + likelihood refinement
```

Interpretation:

```text
If moment/signature clustering separates hidden omega(j):
  Passive observations contain quotient signal.
  Optimization or parameterization is likely the bottleneck.

If moment/signature clustering does not separate hidden omega(j):
  Passive observations may be weakly identifying.
  Full hardening may still help, but expectations should be calibrated.
```

Stage 2A.0.5 decision gate:

```text
If passive signatures separate omega(j):
  Use the signatures as audited initialization or diagnostics for Stage 2A.1.

If passive signatures fail:
  Still run Stage 2A.1, but record that the passive identifiability audit is
  weak and prioritize Stage 2A.2 if hardening fails.
```

## Stage 2A.1: Hardening Study

Question:

```text
Can recovery-biased optimization recover omega(j) when the free soft assignment
fits likelihood but fails quotient recovery?
```

This is not part of the Stage 2A.0 claim. It is a follow-on study for the
observed failure mode where NLL is good but ARI/NMI are poor.

Allowed interventions:

- local-logit warm starts using observations only.
- temperature annealing for assignment softmax.
- hard or straight-through assignments.
- alternating hard-assignment updates.
- row-entropy penalties.
- light prototype-mass balancing.
- prototype separation penalties.
- stricter `disc_soft` residual control.

Required guardrails:

- hidden `omega(j)` must not enter the learner, initializer, feature selection,
  or objective.
- hidden `omega(j)` may be used only by the evaluator for ARI/NMI.
- initializer and hardening schedule must be audited.
- success still requires ARI/NMI plus oracle-close heldout NLL.

Suggested Stage 2A.1 experiments:

```text
DISC04_hardening_random_vs_local_init
DISC05_temperature_annealing
DISC06_straight_through_assignment
DISC07_balance_and_separation_regularization
DISC08_disc_soft_residual_control
```

Stage 2A.1 decision gate:

```text
If hardening recovers omega(j) and preserves oracle-close NLL:
  Claim recovery only for the hardened regime.
  Consider Stage 2A.2 to understand identifiability.

If hardening still fails:
  Treat passive observations as weakly identifying for the tested quotient.
  Prioritize Stage 2A.2.
```

## Stage 2A.2: Identifiability-Aware Discovery

Question:

```text
Can the experiment or assignment structure be designed so hidden quotient
recovery becomes identifiable?
```

Stage 2A.2 is not merely optimizer tuning. It changes the information structure
or assignment constraints to test whether quotient recovery can be made easier
or more principled.

### DISC09 Active Probe Design

Goal:

```text
Design synthetic probe contexts that increase quotient separability.
```

Possible probe axes:

- synthetic noise regimes.
- code family, basis, distance, or rounds.
- local-window families.
- detector/logical support windows.
- teacher prototype separation.
- controlled residual perturbations.

Possible selection criteria:

- prototype separation.
- Fisher-information-like sensitivity.
- pair-correlation contrast.
- local-window likelihood curvature.
- KL or TVD contrast under candidate perturbations.

### DISC11 OT/Sinkhorn Assignment

Goal:

```text
Replace independent row-softmax assignments with constrained transport over a
visible DEM fault graph.
```

Concept:

```text
min_S <S, C> + tau H(S) + lambda_graph Tr(S^T L_fault S)
subject to row and prototype-mass constraints
```

Compare:

```text
free_softmax
free_softmax + entropy/balance
hard or straight-through assignment
OT/Sinkhorn
OT/Sinkhorn + graph smoothness
```

### DISC12 Multi-Environment Invariant Quotient

Goal:

```text
Share quotient assignments across environments while prototype strengths vary.
```

Model sketch:

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

Guardrail:

```text
Invariance alone is not proof of latent quotient recovery.
```

Stage 2A.2 decision gate:

```text
If active probes or structured assignments improve ARI/NMI at oracle-close NLL:
  Report which identifiability intervention is necessary.

If none improve recovery:
  Treat the tested hidden quotient as not recoverable under the current
  observation and model contract.
```

## Stage 2A Closure

Current closure:

```text
Direct shared-assignment likelihood learning does not recover hidden omega,
even though local inverse logits contain substantial target signal.
```

This closure follows the diagnostic chain:

```text
2A.0:
  likelihood can match without partition recovery

DISC10:
  passive visible signatures contain weak quotient signal

2A.1:
  hardening does not improve beyond the local-logit initializer ceiling

DISC12:
  multi-environment shared S gives only weak recovery gains

DISC13:
  target mismatch is not confirmed; oracle logits contain omega

DISC13b:
  fitted local logits contain substantial target signal
  but direct S/alpha learning still underperforms
```

Do not spend the next iteration on more entropy, balance, separation, passive
alpha sweeps, or OT/Sinkhorn directly on `S` as the main path. Those target the
wrong bottleneck.

## Stage 2C: Local Inverse Representation Discovery

Question:

```text
Can fitted local inverse representations be denoised, factorized, and
clustered better than direct S/alpha likelihood learning?
```

First experiment:

```text
DISC15_local_logit_to_mechanism_discovery
```

Input:

```text
local logits or local response fingerprints
```

Representations:

- single-environment local logits.
- multi-environment local-logit matrix `L[j,e]`.
- structural plus local-logit combined features.
- graph-smoothed local logits over the visible DEM fault graph.
- PCA-denoised local logits.

Methods:

- deterministic k-means.
- spectral similarity embedding plus k-means.
- sparse dictionary / NMF-style nonnegative factorization.
- graph-Laplacian smoothing plus clustering.
- overlapping mechanism codes.

Primary baseline:

```text
local-logit clustering:
  ARI 0.5187
  NMI 0.8287
```

Success:

```text
beats baseline:
  ARI > 0.5187
  NMI > 0.8287

strong:
  ARI >= 0.80
  NMI >= 0.80
```

If DISC15 beats the baseline under observable-only selection, the validated
path becomes:

```text
local inverse first, mechanism discovery second
```

If DISC15 cannot beat local logits, proceed to active observability.

Current DISC15 result:

```text
evaluator_only_candidate_beats_baseline_no_observable_selection_claim
```

The visible `local_logit_probability` representation reached:

```text
ARI 0.7923
NMI 0.9245
```

against the declared local-logit baseline:

```text
ARI 0.5187
NMI 0.8287
```

and the measured train-env local-logit baseline:

```text
ARI 0.5739
NMI 0.8618
```

This validates the local-inverse-first direction as promising, but it is not
yet a deployable success because the observable-only selection score chose a
worse single-environment representation. The next Stage 2C refinement should
predefine a stronger observable representation-health criterion before making
a main claim.

DISC15c confirmatory result:

```text
predeclared representation: local_logit_probability
candidate selection: disabled
result: near_strong_confirmed

local_logit baseline:
  ARI 0.5739
  NMI 0.8618

local_logit_probability:
  ARI 0.7923
  NMI 0.9245
```

This confirms that the stronger Stage 2C representation is real and not merely
an evaluator-selected artifact. It remains just below the strong ARI threshold,
so the next synthetic gate is active local-inverse observability.

## Stage 2D: Active Local-Logit Observability

Question:

```text
Which probes improve recoverability of local inverse logits?
```

This replaces the older passive contrast framing. DISC12b increased
between-environment observable contrast, but recovery did not track contrast
monotonically. Stage 2D should instead ask whether probes improve local inverse
representation quality.

Metrics:

- `corr(local logits, oracle logits)`.
- `R2(local -> oracle)`.
- ARI/NMI of clustered local logits.
- local-logit cluster margin.
- eigen-gap / singular spectrum of `L[j,e]`.
- heldout environment transfer.

If active probes improve these local-logit metrics, then mechanism discovery
gets a stronger representation. If they do not, close hidden-omega recovery
under the current synthetic observation family and reframe discovery as
predictive/observational structure learning.

### DISC16a Shot-Budget Sweep

Question:

```text
Can more local inverse evidence turn DISC15c ARI 0.7923 into ARI >= 0.80?
```

Current result:

```text
strong_recovery_by_predeclared_local_inverse_probability

shots   ARI  NMI  active  bootstrap NMI  probability variance
25k     1.0  1.0  9       1.0            0.003372
50k     1.0  1.0  9       1.0            0.001334
100k    1.0  1.0  9       1.0            0.0008979
200k    1.0  1.0  9       1.0            0.0005264
500k    1.0  1.0  9       1.0            0.0001955
```

Conclusion:

```text
Strong synthetic quotient recovery is achieved by the predeclared local inverse
probability representation once the local inverse estimator has enough
evidence. The direct S/alpha likelihood route remains closed as a failure, but
the local-inverse-first route succeeds in this controlled d3/r1 setting.
```

## Stage 2B: Google External Validation

Question:

```text
On real Google data without true omega(j), do discovery models improve heldout
likelihood, calibration, transfer, or decoder-facing utility?
```

Google data can evaluate:

- heldout detector/logical likelihood.
- detector-rate matching.
- local-correlation matching.
- logical prediction.
- calibration and transfer.
- robustness across samples/time.
- external utility of discovered priors.

Google data cannot evaluate:

```text
true hidden quotient recovery
```

unless a proxy partition is explicitly defined and labelled as a proxy.

Run:

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

Required Google reporting:

- ground-truth partition unavailable.
- ARI/NMI unavailable unless using explicit proxy labels.
- assignment entropy.
- active/dead prototype audits.
- parameter accounting.
- heldout and transfer deltas against local and known-orbit-like baselines.

Google DISC sequence:

```text
GDISC12_multi_context_shared_response:
  multi-context shared response model across sample, patch, basis, cycles,
  time/window, or decoder pathway; no ARI.

GDISC13b_real_local_inverse_audit:
  stability, predictiveness, and prior agreement of real local inverse logits;
  no oracle-logit corr/R2 because Google has no oracle logits.

GDISC15_real_local_mechanism_discovery:
  Stage 2C local-logit mechanism discovery on Google local inverse
  representations; evaluates predictive utility and proxy alignments only.
```

Smoke command:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_google_local_mechanism \
  --dataset-root /home/cx/Document/google_72Q_surface_code_d3_d5_set1 \
  --native-gpu \
  --sample-id sample_00 \
  --patch-id d3_at_q5_5 \
  --basis X \
  --rounds-label r13 \
  --train-shots 4096 \
  --heldout-shots 1024 \
  --steps 40 \
  --subsample-count 2 \
  --subsample-shots 2048 \
  --subsample-steps 30 \
  --max-windows 96 \
  --output-root outputs/google_static
```

Current smoke result:

```text
GDISC15_smoke:
  early_positive_predictive_utility_under_parameter_compression
  continuous_local_inverse_stable
  discrete_cluster_identity_unstable
  proxy_labels_only_no_recovery_claim

GDISC13b:
  mean pairwise local-logit corr 0.9177
  mean pairwise cluster NMI 0.4310

GDISC15:
  selected GDISC15_pca_scores_rank3
  params 99 vs local_full 1341
  heldout excess NLL 0.006583 vs 0.006611
  detector-rate MAE 0.007060 vs 0.007211
  local-correlation error 0.005075 vs 0.005092
  logical flip calibration 0.002853 vs 0.004470
```

Interpretation:

```text
Synthetic hidden-quotient recovery remains difficult, but the local inverse
mechanism representation has early real-data predictive value. This does not
claim true physical mechanism discovery.
```

GDISC15b grid validation:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_google_gdisc15b_grid \
  --dataset-root /home/cx/Document/google_72Q_surface_code_d3_d5_set1 \
  --native-gpu \
  --samples sample_00,sample_01 \
  --patches d3_at_q5_5 \
  --bases X,Z \
  --rounds-labels r13 \
  --heldout-split-types shot-heldout \
  --pca-ranks 1,2,3,5,8 \
  --random-control-ranks 1,2,3,5,8 \
  --output-dir outputs/google_static/GDISC15b_google_grid_validation
```

Current GDISC15b small-grid result:

```text
completed contexts: 4
local_full params: 1340.0 +/- 1.155
compressed params: 98.5 +/- 0.577

GDISC15_local_logit:
  heldout excess NLL delta vs local_full: +0.00000165
  wins/total: 0/4

GDISC15_pca_scores_rank3/5/8:
  heldout excess NLL delta vs local_full: +0.0000381
  detector MAE improves on mean
  wins/total: 1/4

random low-rank controls:
  worse than local inverse models
```

Current interpretation:

```text
The compressed local inverse models preserve local_full performance under
strong parameter compression, but do not yet produce consistent paired
heldout-NLL wins. The Stage 2B evidence is promising for compression and
stability, not yet robust predictive improvement.
```

Stage 2B decision gate:

```text
If discovery improves real-data likelihood/calibration/transfer:
  Claim external predictive validation of discovered DEM-fault sharing
  structure.

Do not claim true quotient recovery from Google data.
```

## Publishable Outcome Categories

Stage 2 should be written so that negative results are coherent rather than
treated as failures that always require another method.

| Outcome | Result | Claim |
| --- | --- | --- |
| A | Stage 2A.0 succeeds | Free assignment can recover a synthetic hidden quotient under fixed DEM/Bernoulli observations. |
| B | Stage 2A.0 fails, Stage 2A.1 succeeds | Quotient recovery requires recovery-biased optimization or parameterization. |
| C | Stage 2A.1 fails, Stage 2A.2 succeeds | Quotient recovery requires identifiability-aware probes or structured assignment. |
| D | Stage 2A.2 fails, Stage 2B succeeds | Discovery improves prediction, calibration, transfer, or utility, but does not recover the hidden quotient. |
| E | All fail | The current observation/model contract is insufficient for quotient discovery. |

## Prioritization

Immediate priority:

```text
1. Report Stage 2A.0 cleanly.
2. Run Stage 2A.0.5 passive identifiability audit.
3. Run DISC10 moment/spectral seed.
4. If recovery-negative, implement Stage 2A.1 hardening.
5. If hardening is insufficient, prototype Stage 2A.2 active-probe and
   structured-assignment diagnostics.
6. Keep Stage 2B as external predictive validation only.
```

Recommended order for new Stage 2 work:

```text
1. Stage 2A.0 clean report.
2. Stage 2A.0.5 passive identifiability audit.
3. DISC10 moment/spectral seed.
4. Stage 2A.1 local warm start and hardening.
5. DISC09 active probe design.
6. DISC11 OT/Sinkhorn assignment.
7. DISC12 multi-environment invariant quotient.
8. Stage 2B external validation and decoder-facing utility, only as external
   value evidence.
```

## One-Line Summary

```text
Stage 2 first asks whether free S recovers omega; if not, harden the recovery
procedure; if that still fails, redesign the identifiability problem; use Google
only for external predictive validation.
```

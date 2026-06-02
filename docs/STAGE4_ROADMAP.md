# Stage 4 Roadmap: Bridge Survival Before Neural

Stage 4 introduces neural syndrome-response discovery only after the visible
surface has proven that catalog mechanism structure, or a valid observational
quotient of it, survives the Google-shaped projection.

The first Stage 4 deliverable is therefore not a neural model. It is a
synthetic Google-shaped `S3A_protocol_freeze` plus protocol and
mechanism-survival audits. Neural source pretraining and Google transfer are
allowed only after this bridge artifact passes its contract gates.

## Core Questions

Stage 4 is judged by three questions, in this order:

```text
1. Does the Google-shaped projection preserve catalog mechanism or quotient
   structure?

2. Does Attention-VQ improve source visible replay without using evaluator
   labels?

3. Does frozen source structure transfer to Google V2 better than
   random-codebook, train-on-Google-only, and global-null controls?
```

Average replay score is not the central claim by itself. It is supporting
evidence for these three decisions. A run that improves mean replay while
failing the projection-survival, no-evaluator-label, or frozen-transfer control
tests is not an S4 pass.

## Claim Boundary

S4 remains a visible-observation discovery stage. The learner path may consume
only frozen visible features and approved public context fields. Evaluator-only
mechanism labels, quotient labels, channels, PTMs, Kraus matrices, oracle
prototypes, teacher IDs, path/sample/context surrogate IDs, and decoder
correctness fields must not enter training or model selection.

Google V2 has no ground-truth `M*` mechanism labels. S4 may claim improved
no-oracle replay of public Google syndrome-response structure and audited
source-to-Google prototype transfer. It must not claim true Google physical
mechanism recovery or Google `M*` label recovery.

## Milestone Gates

### S4.0 Bridge Freeze

Build a synthetic Google-shaped `S3A_protocol_freeze` from a controlled catalog
teacher and prove the artifact is learner-safe and compatible with the real
Google V2 visible surface.

Required decision and artifacts:

- `synthetic_freeze_decision`
- `forbidden_feature_audit.json`
- `schema_compatibility_with_google_v2`
- `visible_features.npy`
- `sampled_visible_features.npy`
- `visible_feature_schema.json`
- `visible_feature_matrix.json`
- `split_manifest.json`
- `source_label_manifest.json`
- `source_evaluator_labels.json`
- `adequacy_report.json`
- `acceptance_audit.json`
- `metrics.json`
- `summary.md`

Minimum pass:

- the synthetic freeze is Stage-3A-compatible;
- forbidden learner fields count is zero;
- evaluator-only source labels are absent from learner-visible files;
- synthetic and Google V2 schemas, block slices, dtypes, dimensions, and
  normalization policies are compatible or explicitly rejected.

### S4.0.5 Surface Survival Audit

Before neural training, audit whether the Google-shaped projection preserves the
known catalog mechanism structure or a scientifically valid quotient/alias
structure.

Required decision and artifacts:

- `source_ceiling_decision`
- `mechanism_survival_report.json`
- `projection_alias_classes`
- `projection_collapse_matrix`
- `alias_ceiling.json`
- `source_visible_ceiling.json`
- `source_alias_classes.json`
- `source_baseline_results.json`
- `source_projection_adequacy.json`

Required evaluator-only metrics:

- visible ceiling ARI/NMI;
- quotient ceiling ARI/NMI;
- source-label linear probe accuracy;
- source-label kNN accuracy;
- prototype purity;
- silhouette by mechanism label;
- blockwise mutual information with evaluator-only labels;
- alias-class map;
- mechanism collapse matrix.

Decision labels:

- `bridge_surface_pass`: exact or near-exact mechanism structure survives.
- `bridge_surface_quotient_only`: exact labels collapse, but quotient structure
  survives.
- `bridge_surface_projection_aliasing`: systematic projection aliasing is
  present and documented.
- `bridge_surface_fail`: the visible surface does not preserve the discovery
  target; S4.1 and S4.2 mainline runs must not proceed.

### S4.1 Source Neural Pretrain

Train source models only from the S4.0 frozen visible matrix and learner-visible
public context fields. Evaluator labels may be used only after training for
audit reports.

Required decision and artifacts:

- `source_pretrain_decision`
- `mlp_continuous` vs `attention_vq`
- `codebook_usage.json`
- `prototype_cards.json`
- `model_selection_audit.json`
- `source_replay_metrics.json`
- `controls.json`
- `seed_stability.json`
- `acceptance_audit.json`

Selection rule:

- model selection uses validation visible replay only;
- ARI, NMI, balanced accuracy, min recall, mechanism labels, quotient labels,
  and alias labels are posthoc evaluator-only audits;
- `attention_vq` should improve source visible replay relative to
  `mlp_continuous`, global/mean-only, assignment shuffle, feature scramble,
  context shuffle, and public-stratified null controls before it can be treated
  as the mainline source bundle.

Default Attention-VQ contract:

- block-token encoder;
- `K = 32`;
- code dimension `32`;
- VQ commitment loss;
- auditable codebook usage and prototype cards;
- seed-stability audit.

### S4.2 Frozen Google Transfer

Apply the S4.1 source bundle to a real Google V2 `S3A_protocol_freeze`. The main
claim path is strict frozen transfer: freeze standardization, tokenizer/encoder,
and codebook; train only a low-capacity calibrator and replay heads.

Before interpreting a transfer failure, run the support alignment audit. It
checks whether real Google rows occupy the frozen source coordinate support,
whether public-geometry metadata has been mirrored, whether feature marginals
were aligned using visible-only Google statistics, and whether Google rows use
more than a collapsed subset of source codes.

Required decision and artifacts:

- `google_transfer_decision`
- strict frozen transfer vs controls
- `claim_boundary.json`
- `coordinate_system_audit.json`
- `replay_head_audit.json`
- `source_google_support_report.json`
- `block_shift_ranking.json`
- `domain_classifier_audit.json`
- `nearest_source_coverage.json`
- `codebook_google_coverage.json`
- `google_transfer_metrics.json`
- `control_margin_metrics.json`
- `transfer_acceptance_audit.json`
- `summary.md`

Required controls:

- train-on-Google-only;
- random codebook or random adapter;
- global/mean-only;
- assignment shuffle;
- feature scramble;
- context shuffle;
- public-stratified null.

Required `claim_boundary.json` fields:

```json
{
  "claims_true_google_physical_mechanism_recovery": false,
  "claims_google_m_label_recovery": false,
  "claims_visible_syndrome_response_replay": true,
  "claims_source_to_google_prototype_transfer": true,
  "google_ground_truth_mechanism_labels_available": false
}
```

Minimum pass:

- frozen source structure beats train-on-Google-only or at least random-codebook
  transfer;
- the margin holds on both `raw_target_only` and `block_normalized` replay;
- no forbidden or evaluator-only Google label path is present;
- the final claim does not state true Google physical mechanism recovery.

### S4.3 Transfer Diagnostics

S4.3 explains transfer success or failure. It does not replace the S4.2 main
claim path.

Required decision and artifacts:

- `transfer_diagnostics_decision`
- strict frozen vs frozen-codebook-adapter comparison
- `domain_shift_report`
- `failure_taxonomy`
- `transfer_diagnostics.json`

Legal diagnostic modes:

- `strict_frozen_transfer`: freeze standardization, encoder, and codebook; train
  calibrator and replay heads only.
- `frozen_codebook_train_adapter`: freeze codebook; allow a low-capacity
  affine/block adapter plus calibrator and replay heads.

Failure taxonomy:

- `normalization_or_domain_shift`: strict frozen transfer fails, but frozen
  codebook plus adapter passes.
- `source_google_surface_mismatch`: both transfer modes fail and S4.0.5 reports
  projection aliasing or low source ceiling.
- `source_prototype_non_transfer`: source pretrain passes but neither transfer
  mode beats random-codebook or train-on-Google-only controls.
- `model_capacity_or_training_failure`: source ceiling is high, transfer surface
  is adequate, but trained models underperform simple visible-only baselines.

### S4.6 Google-Unit Source Expansion

S4.6 repairs the source/Google support mismatch by constructing a controlled
source teacher at the Google public signature assignment unit. It is a
visible-source expansion milestone, not a physical-channel generation claim.

Required decision and artifacts:

- `stage4_google_unit_source_expansion_decision`
- `mode_design_split_manifest.json`
- `mode_design_audit.json`
- `visible_surrogate_transform_audit.json`
- `mixture_mode_survival_report.json`
- `google_native_mode_coverage.json`
- `source_google_mode_distance.json`
- `expanded_transfer_report.json`
- `paired_bootstrap_report.json`
- `seed_split_repeat_report.json`
- `stronger_statistical_controls_report.json`
- `mechanism_source_structure_ablation_report.json`
- `robustness_closeout_report.json`
- `acceptance_audit.json`
- `S3A_protocol_freeze/`

Split rule:

- missing-mode selection uses only the Google `design` split;
- calibrator/replay heads may use only the `validation` split;
- final transfer and gap closure are reported only on `heldout_eval`;
- `S3A_protocol_freeze/` contains only the frozen visible matrix, schema,
  split, forbidden audit, learner/evaluator manifests, and claim boundary.

Required S4.6 controls:

- `control_public_context_only`;
- `control_random_mixture_same_context`;
- `control_shuffled_google_native_mode`;
- `control_family_bucket_shuffled`;
- `control_no_visible_transform`;
- `control_target_mean_std_only`.

S4.6 also reports `dmle_qec_visible_marginal_mle` as a baseline comparator.
Because S4.6 consumes frozen public syndrome-response signatures rather than a
DEM parity-map likelihood object, this is a visible-surface projection of the
dMLE-style independent marginal MLE baseline, not the full upstream
DMLE-QEC TensorNetwork/DEM implementation.

S4.6 robustness closeout:

- `paired_bootstrap_report.json`: paired heldout-row bootstrap for strict and
  adapter transfer against controls.
- `seed_split_repeat_report.json`: repeated design/validation/heldout splits
  with redesigned source modes.
- `stronger_statistical_controls_report.json`: strict transfer against
  public-context, random-mixture, target-mean/std, dMLE-style marginal, random
  codebook, global-null, and train-on-Google-only controls.
- `mechanism_source_structure_ablation_report.json`: no-transform,
  family-bucket-shuffle, native-mode-shuffle, random-mixture, and public-only
  ablations.
- `robustness_closeout_report.json`: final robustness decision.

Robustness decisions:

- `s4_6_robust_positive`: mechanism/source structure and transfer remain stable
  against controls, including target-native train-on-Google.
- `s4_6_robust_source_structure_positive_target_native_dominates`: source
  structure is stable against mechanism/marginal/random/global controls, but
  target-native train-on-Google remains stronger.
- `s4_6_current_split_positive_only`: current split is positive but robustness
  gates do not all pass.
- `s4_6_robustness_inconclusive`: current split or robustness evidence is not
  sufficient.

Any deterministic visible shape transform must be recorded as a
`visible_surrogate_shape_transform` with `claims_physical_channel_sampling` and
`claims_cptp_gksl_generation` set to `false`.

## Public Interfaces

Expected Stage 4 configs:

```text
configs/scope_static/stage4_synthetic_google_surface_v1.yaml
configs/scope_static/stage4_source_ceiling_v1.yaml
configs/scope_static/stage4_source_pretrain_v1.yaml
configs/scope_static/stage4_support_audit_v1.yaml
configs/scope_static/stage4_assignment_geometry_v1.yaml
configs/scope_static/stage4_google_unit_source_expansion_v1.yaml
configs/scope_static/stage4_google_transfer_v1.yaml
configs/scope_static/stage4_transfer_diagnostics_v1.yaml
```

Expected Stage 4 commands:

```text
scope-stage4-synthetic-freeze
scope-stage4-source-ceiling
scope-stage4-source-pretrain
scope-stage4-support-audit
scope-stage4-assignment-geometry
scope-stage4-google-unit-source-expansion
scope-stage4-google-transfer
scope-stage4-transfer-diagnostics
```

Shared S4 artifact readers live behind `scope_static.mechanism_discovery`.
Stage 4 code must not ad hoc parse evaluator-only labels from learner-safe
files.

## Minimum S4 V1 Pass Conditions

- S4.0 synthetic Google-shaped freeze is Stage-3A-compatible.
- `forbidden_feature_audit.json` passes with zero forbidden learner fields.
- Evaluator-only source labels are absent from learner-visible files.
- S4.0.5 shows that the synthetic Google-shaped projection preserves mechanism
  or quotient structure above controls.
- S4.1 shows that Attention-VQ improves source visible replay without using
  evaluator labels for training or model selection.
- S4.2 shows that frozen source structure transfers to Google V2 better than
  random-codebook, train-on-Google-only, and global-null controls.
- `claim_boundary.json` and the final report never state true Google physical
  mechanism recovery or Google `M*` label recovery.

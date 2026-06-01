# Stage 3 Roadmap: Mechanism-Structure Discovery

Stage 3 tests whether SCOPE-Discovery can learn a latent mechanism quotient
from learner-visible observations without direct mechanism-label supervision.
Discovery means learning assignments, prototypes, and observational alias
classes from visible data, not predicting a mechanism label that was provided to
the learner.

Stage 2 is closed as a no-leakage physical-mechanism catalog validation stage:
the system can generate controlled noisy QEC observations from declared
mechanisms, verify teacher/catalog separability, and train learner models
that recover and replay learner-visible noisy observation distributions without
oracle leakage. Stage 3 is the next claim boundary: remove direct
mechanism-label supervision and test whether latent mechanism structure can be
inferred from visible observations alone.

## Core Question

```text
Can learner-visible probe observations recover the mechanism structure itself?
```

The Stage 3 learner should infer latent assignments and visible prototypes.
Mechanism IDs, physical-family labels, exact channels, exact PTMs, Kraus
matrices, teacher IDs, teacher-self features, and oracle prototypes are
evaluator-only.

Operationally, Stage 3 is the "+1" object above the toolbox: data preparation
generates teacher-declared noisy QEC observations from a controlled catalog,
learner learns/replays visible noisy observation distributions under no-leakage
guardrails, and Stage 3 must infer the latent mechanism quotient from visible
observations without direct mechanism-label supervision.

If two mechanisms induce the same visible distribution, exact hidden-label
recovery should not be forced. The correct discovery output is an observational
quotient class:

```text
m_a ~_obs m_b  <=>  p(y | m_a) ~= p(y | m_b)
```

Physicality boundary: Stage 3 discovery may reuse catalog unitary/Kraus/readout
mechanism definitions when replaying predicted catalog mechanisms. It should
not claim arbitrary CPTP/GKSL channel generation unless a future learner is
parameterized and audited to enforce that constraint directly. Data are not
`CPTP`; the physical claim is that the data-preparation teacher samples observations from
catalog mechanisms whose generating maps are local CPTP channels, valid
stochastic readout maps embedded into POVMs, or declared valid surrogates with
no silent postselection/renormalization.

## Starting Surface

Stage 3 starts from the accepted learner visible surface:

- Z/X-only probe measurements;
- X-prepared states for phase/coherence observability;
- no Y-basis preparation;
- no Y-basis measurement;
- multi-context batches for drifted mechanisms such as M13;
- raw time-sequence features retained before derived summaries;
- learner-visible operation/instruction context metadata from a fixed public
  instruction alphabet. This is circuit context, not a mechanism label or
  mechanism-instance surrogate ID.

M13 is not a single-context mechanism-recovery target. It is a
context-dependent latent-drift recovery target. Single-context failure is not a
Stage 3 failure by itself; multi-context recovery is the intended test.
When an overcomplete discovery model splits M13 into pure context/drift
submodes, exact one-cluster label recall may be low even though the mechanism
family is not confused with other mechanisms. Reports must distinguish exact
label recall from evaluator-only M13 pure-submode recall.

M14 is the paired operation-dependent control target. Its contract separates
the visible operation axis from the error-generator axis: the first Stage 3
catalog uses an `rx` operation site with an `rz` coherent error generator, so
M14 is not another fixed `rx` overrotation.

Allowed learner inputs:

- preparation label;
- measurement basis label;
- repeat count;
- qubit count;
- empirical probabilities;
- empirical expectations;
- shot count;
- finite-shot uncertainty estimates;
- sampled-observation-derived features.

Forbidden learner inputs:

- true mechanism ID;
- mechanism name;
- physical-family label;
- teacher self-distinguishment features;
- exact channel, Kraus, or PTM matrices;
- oracle prototype vectors;
- hidden drift parameters;
- any identity-derived field.

## Required Objects

Stage 3 should produce:

- learned assignment matrix `S[j, k]` or `Pi[j, k]`;
- learned visible prototypes / cluster representatives;
- quotient or alias classes for observationally indistinguishable mechanisms;
- heldout visible-generation model;
- evaluator-only ARI/NMI/BA/min-recall reports;
- prototype quality metrics;
- leakage audit showing labels/channels/oracle features were not used by the
  learner;
- no-leakage and protocol-validity audits;
- physicality audit references when generated replay uses catalog mechanisms.

Assignment index rule:

- `j` indexes the protocol-declared unit of assignment.
- For the first Stage 3 pass, `j` should be one mechanism-condition instance or
  generated probe-batch instance.
- `k` indexes a learned latent mechanism/prototype.
- Do not make `j` a single shot in the first pass; single-shot assignment is
  noisier and less aligned with the current probe-batch feature surface.
- Each experiment must declare whether `j` means a mechanism-condition,
  probe-batch, context-window, or another visible instance type before training.

## Work Packages

### Stage 3A: Dataset And Protocol Freeze

Freeze the learner-visible dataset contract.

Deliverables:

- visible feature schema;
- frozen learner-visible feature matrix (`visible_features.npy`);
- frozen sampled-visible comparator matrix (`sampled_visible_features.npy`);
- visible feature matrix manifest;
- operation-context publicness audit;
- probe schedule manifest;
- batch/context schema;
- train/validation/test split policy;
- protocol-declared assignment unit for `j`;
- leakage guardrail audit.

Acceptance:

- no forbidden learner fields;
- operation context is derived only from public instruction context and cannot
  encode mechanism ID, record ID, location ID, qubits, circuit ID, or slot ID;
- split policy is fixed before model training;
- multi-context batch protocol is explicit;
- assignment unit is declared before model training.

### Stage 3A.5: Observability And Alias Ceiling

Before training discovery models, compute the maximum recoverable quotient from
the learner-visible surface.

Deliverables:

- pairwise visible-distance matrix between true mechanisms;
- oracle-visible clustering under the approved feature surface;
- alias-class map;
- ceiling ARI/NMI/BA/min-recall against exact labels and quotient labels;
- report of mechanisms that are theoretically indistinguishable under the
  current probe surface.

Acceptance:

- exact-label Stage 3 claims are allowed only when the visible ceiling separates
  the mechanisms;
- otherwise the target is quotient recovery, not exact mechanism recovery;
- alias classes are fixed before model training and treated as evaluator-only
  ceiling information.

### Stage 3B: Unsupervised Assignment Recovery

Train discovery models without mechanism-label supervision.

K-selection protocol:

- fixed-K oracle-count run: evaluator declares `K` only as catalog cardinality,
  not labels;
- overcomplete-K run: `K_max > K_true`, with pruning/merge by assignment mass
  and visible distance;
- quotient-K run: accepted `K` may be smaller than `K_true` if alias classes
  exist.

First implementation modes:

- Mode A: `K =` known number of catalog mechanisms;
- Mode B: `K_max = 2 *` known number of catalog mechanisms, then merge/prune.

Model selection may use:

- validation visible NLL;
- validation reconstruction/generation loss;
- assignment entropy and active-prototype regularity;
- stability across seeds on visible-only criteria.

Model selection may not use:

- validation/test ARI;
- validation/test NMI;
- validation/test BA after label matching;
- validation/test min recall;
- oracle-label prototype quality.

### Stage 3B.0: Non-Learned Clustering Baselines

Run auditable visible-only baselines before learned discovery models.

Baselines:

- Gaussian mixture with diagonal covariance;
- Gaussian mixture with full covariance;
- k-means or prototype baseline on visible feature vectors;
- global-null and mean-only controls.

Artifacts:

- `baseline_results.json`;
- `learned_assignments.npy`;
- `baseline_assignments.npz`;
- `learned_assignment_summary.json`;
- `controls.json`;
- `evaluator_only_label_metrics.json`;
- `quotient_metrics.json`;
- `model_selection_audit.json`.

Acceptance:

- baselines use the same frozen visible feature schema and splits;
- evaluator-only ARI/NMI/BA/min-recall are reported after training;
- validation/test label metrics are not used for baseline selection;
- baseline failures identify aliasing, feature weakness, or optimization limits.

### Stage 3B.1: First Discovery Model

Train the first learned discovery model.

Initial model:

- prototype mixture on visible feature vectors;
- learned covariance;
- visible-generation or reconstruction loss;
- quotient-aware assignment hardening.

First implementation:

- diagonal-covariance visible prototype mixture;
- annealed soft assignment matrix `Pi[j,k]`;
- training from the frozen Stage 3A `visible_features.npy` matrix, not
  regenerated mechanism records;
- declared operation-context feature weighting in the visible objective, used
  to keep operation-dependent/crosstalk context from being drowned out by the
  larger probability feature block;
- context-balanced assignment candidate that enforces one visible instance per
  latent prototype per context group when the Stage 3A protocol is balanced;
- K-mode selection by validation visible NLL plus visible-only complexity
  and context-balance penalties;
- declared cap on Stage 3A validation folds for the first operational run;
- declared first-run iteration budget, with seed/fold robustness deferred to
  Stage 3D;
- evaluator-only exact-label and quotient-label reports after fitting.

Artifacts:

- `candidate_selection.json`;
- `visible_feature_matrix.json`;
- `learned_assignments.npy`;
- `learned_prototypes.json`;
- `learned_covariances.npy`;
- `model_parameters.npz`;
- `prototype_generation_metrics.json`;
- `assignment_hardening_audit.json`;
- `label_permutation_audit.json`;
- `model_selection_audit.json`;
- `evaluator_only_label_metrics.json`;
- `context_dependent_mechanism_diagnostics.json`;
- `quotient_metrics.json`.

Later candidates:

- contrastive context-consistency objective for M13/multi-context drift;
- local-inverse representation clustering.

Acceptance:

- evaluator-only ARI/NMI reported;
- selected model is not chosen by validation/test labels;
- validation visible NLL may be used for model selection;
- label permutation is handled explicitly;
- selected `K` follows the declared K-selection protocol;
- failure reports quotient alias classes instead of forcing exact labels.

### Stage 3C: Prototype And Generator Learning

Learn visible prototypes that can generate heldout probe observations.
The first implementation is conditional visible replay: fold-local generators
are fit on Stage 3A train folds from frozen `visible_features.npy` and Stage
3B.1 `learned_assignments.npy`, then scored on validation+test heldout rows.
This is not an unconditional future-context prediction claim.

Metrics:

- categorical population NLL over raw visible outcome groups;
- Gaussian density NLL on visible features as a secondary continuous-density
  diagnostic;
- population cross entropy;
- raw visible-feature MAE;
- population MAE;
- expectation MAE;
- prototype stability across seeds and folds.

Acceptance:

- heldout generation beats global-null and mean-only baselines;
- prototype quality is reported for predicted assignments and oracle-label
  comparators separately;
- oracle comparators remain evaluator-only.
- predicted-assignment generation does not rebuild visible features from
  oracle records and does not use mechanism labels, channels, PTMs, Kraus
  matrices, teacher IDs, or oracle prototypes.

### Layer1.P: Physical Teacher Gate

Before Stage 3D robustness is cited as physical-teacher evidence, the teacher
artifact should be generated by the first-class `Layer1.P_teacher` path. This
path validates the local CPTP/POVM mechanism contract before sampling, runs
full-circuit CUDA-Q Born-rule sampling, and then runs
`Layer1.P_teacher_physicality_audit` as a blocking post-sampling gate.

Acceptance:

- pre-sampling `layer1p_pre_sampling_contract.json` passes;
- generation writes `layer1p_teacher_contract.json`;
- all local unitary/Kraus channels pass Choi positivity and trace-preservation
  checks within declared tolerance;
- all readout modules are valid stochastic maps and equivalent POVMs;
- reset/prep and leakage-surrogate modules have no silent projection or
  renormalization;
- circuit-level sampled output distributions are nonnegative and normalized;
- `teacher_physicality_passed = true`;
- `mechanism_failures = 0`;
- `silent_renormalization_used = false`;
- `leakage_unaccounted_mass = 0`;
- `all_probability_distributions_valid = true`.

### Stage 3D: Quotient Evaluation And Robustness

Evaluate quotient recovery with evaluator-only labels and prove the result is
not accidental.

Implementation order:

1. `S3D.1` assignment-shuffle generator audit;
2. `S3D.2` feature-scramble audit;
3. `S3D.3` context-shuffle audit;
4. `S3D.4` K undercomplete/exact/overcomplete stress;
5. `S3D.5` finite-shot sensitivity;
6. `S3D.6` seed/fold stability;
7. `S3D.7` M13/M14 targeted robustness;
8. `S3D.8` covariance-floor / likelihood-degeneracy audit.

The first control is the assignment-shuffle generator audit:

- keep the frozen Stage 3A visible feature matrix fixed;
- shuffle the discovered Stage 3B.1 assignment rows;
- refit and evaluate the Stage 3C generator;
- compare original-assignment, shuffled-assignment, global-null, and mean-only
  generation metrics.

Expected result:

- `categorical_population_nll` should degrade after assignment shuffle;
- replay metrics should collapse toward the global-null baseline;
- assignment column mass should be preserved, so the audit breaks row alignment
  rather than the marginal prototype distribution.

Purpose:

- verify that S3C replay comes from discovered latent structure rather than an
  unconditional generator, assignment-mass marginal, or metric artifact.

The second control is the feature-scramble audit:

- keep the Stage 3B.1 discovered assignment matrix fixed;
- row-scramble the frozen Stage 3A visible feature matrix;
- preserve the visible feature row distribution while breaking row alignment
  with the assignments;
- refit and evaluate the Stage 3C generator;
- compare original-assignment, scrambled-feature, global-null, and mean-only
  generation metrics.

Expected result:

- `categorical_population_nll` should degrade after feature scrambling;
- replay metrics should collapse toward the global-null baseline;
- the feature-row multiset should be preserved, so the audit breaks
  feature-assignment alignment rather than changing the marginal visible
  distribution.

Purpose:

- verify that S3C replay comes from the discovered latent structure aligned to
  the correct visible observations rather than from an unconditional generator,
  row-distribution artifact, or metric artifact.

The third control is the context-shuffle audit:

- keep frozen Stage 3A visible features fixed;
- keep the Stage 3B.1 discovered assignment matrix fixed;
- row-shuffle only Stage 3A protocol `context_group` labels;
- rebuild grouped validation/test folds from the shuffled context groups;
- refit and evaluate the Stage 3C generator;
- compare original grouped-context, context-shuffled, global-null, and
  mean-only generation metrics.

Expected result:

- for the current context-free selected B1 model, context-shuffled
  pseudo-context folds should remain meaningfully above null and the original
  grouped-context split should not be artificially easier;
- if a future selected model uses context groups directly, the same audit must
  report whether context shuffling damages the context-conditioned claim;
- `context_group` remains a protocol-only field, not a learner-visible feature.

Purpose:

- verify that S3C replay is not an artifact of an overly easy context split or
  hidden context-label leakage.

The fourth control is the K-stress audit:

- rerun visible-only prototype discovery at fixed K values;
- include an undercomplete K below the Stage 3A.5 quotient count;
- include exact catalog-cardinality K;
- include overcomplete K, currently `2 * catalog_cardinality` capped by record
  count;
- score evaluator-only exact/quotient recovery after fitting;
- score heldout visible generation for each K against global-null and mean-only
  baselines.

Expected result:

- exact and overcomplete K preserve mechanism or quotient recovery;
- exact and overcomplete K preserve heldout visible replay above null;
- undercomplete K degrades recovery when the quotient size is too small;
- undercomplete K may still generate visible observations well, so recovery and
  generation must be reported separately.
- exact-K failures must report whether they come from missing visible
  operation context, missing probe quadrature, or a genuine structured-model
  limitation.

Purpose:

- verify that Stage 3 discovery is not an artifact of a single lucky K choice,
  and document the recoverable K range before claiming latent mechanism
  structure.

The fourth-b control is the overcomplete merge/prune audit:

- consume the overcomplete assignment matrix from Stage 3D.4;
- prune inactive clusters;
- keep macro clusters separate;
- merge only declared assignment microclusters into a visible-only tail-submode
  family;
- score post-merge exact/quotient recovery and heldout visible generation;
- keep mechanism labels out of the merge rule and use them only after the merge
  map is fixed.

Expected result:

- overcomplete microclusters that represent one context/drift family can be
  merged without label supervision;
- post-merge family count drops toward the mechanism/quotient scale;
- post-merge recovery improves without destroying heldout visible generation;
- if rare mechanisms are also microclusters, the audit must fail or report an
  unsafe merge rather than hiding the ambiguity.
- applying this audit to exact-K assignments is allowed as a boundary test, but
  exact-K need not contain mergeable microclusters; failure there is evidence
  that merge/prune is not the right repair for that K setting.

Purpose:

- distinguish scientifically valid visible-only submode consolidation from
  label-informed post-hoc relabeling.

Acceptance:

- accepted result survives seed/fold changes;
- M13 is only expected to be fully recoverable in multi-context mode;
- observational aliases are reported as quotient classes, not forced labels;
- S3D.1 passes before S3C replay is described as assignment-structure
  dependent;
- S3D.2 passes before S3C replay is described as feature-assignment alignment
  dependent;
- S3D.3 passes before S3C replay is described as context-split robust;
- S3D.4 passes before Stage 3 recovery is described as K-robust;
- S3D.4b passes before overcomplete subclusters are described as recoverable
  mechanism families;
- failures identify observability, optimization, or protocol limits.

### Stage 3E: Scale And External Validation

Extend after the synthetic Stage 3 claim is stable.

Targets:

- larger allM artifacts;
- additional circuit depths and supports;
- Google/surface-code proxy validation;
- decoder-facing utility tests;
- cross-context transfer audits.

These are not required for the first Stage 3 discovery pass. Google/surface-code
datasets contain real measurement-derived detection events, observable flips,
Stim circuits, noisy SI1000 circuits, metadata, and decoder priors/pathways, but
they do not by themselves provide ground-truth physical mechanism labels for
Stage 3 discovery.

Current Google Stage 3 closeout adapter:

```bash
scope-google-s3-visible-cache-v2 --config configs/scope_static/google_s3_visible_cache_v2.yaml
scope-google-s3-visible-aggregate-v2 --config configs/scope_static/google_s3_visible_aggregate_v2.yaml
scope-google-s3-visible-adapter-v2 --config configs/scope_static/google_s3_visible_adapter_v2.yaml
```

Acceptance is artifact-contract only:

```text
- `visible_features.npy` is frozen before Stage 3B/3C;
- `visible_feature_schema.json` names learner-visible columns;
- `forbidden_feature_audit.json` blocks context/sample/path surrogate IDs;
- `split_manifest.json` fixes grouped context splits before learner fitting;
- Stage 3 artifact loaders can read the frozen visible matrix.
```

Primary artifacts:

```text
outputs/google_static/google_s3_visible_surface_v2_cache/precompute_cache/
  cache_manifest.json
  source_file_manifest.json
  contexts/cache_context_*.npz

outputs/google_static/google_s3_visible_surface_v2_cache/precompute_cache/aggregates/
  aggregate_manifest.json
  aggregate_context_*.npz

outputs/google_static/google_s3_visible_surface_v2/S3A_protocol_freeze/
  metrics.json
  visible_features.npy
  visible_feature_schema.json
  forbidden_feature_audit.json
  split_manifest.json
  adequacy_report.json
  probe_schedule_manifest.json
```

Historical Google DEM-proxy scorecards are archived separately and are not the
current Google Stage 3 path.

Stage 3 Google V2 closeout claim:

```text
The public syndrome-response V2 surface supports no-oracle replay of raw Google
syndrome-response structure. Raw-target-only scoring beats global/mean-only,
assignment-shuffle, feature-scramble, and public-stratified-null controls. This
is not true physical mechanism recovery because Google data provide no hidden
mechanism partition.
```

The next research stage is S4 neural syndrome-response discovery: use a neural
encoder with an auditable prototype or VQ bottleneck, keep the same no-oracle
and no-surrogate-ID restrictions, and require raw-target-only plus
block-normalized improvements over the S3B1 prototype mixture.

```text
dmle_qec_upstream
```

This is a direct adapter to `/tmp/DMLE-QEC` using the upstream
`TensorNetwork`/`PCM` detector-syndrome DEM MLE path. It is disabled by default
because it requires the upstream dependency stack (`ldpc`, `cotengra`,
`kahypar`, `pymatching`, etc.). When enabled, missing upstream code or
dependencies are hard failures/skipped contexts, not a fallback to
`dmle_qec`.

## Metrics

Primary discovery metrics:

```text
ARI
NMI
balanced accuracy after label matching
min recall after label matching
active prototype count
quotient alias classes
```

Primary generation metrics:

```text
categorical population NLL
visible Gaussian density NLL
population cross entropy
raw visible-feature MAE
population MAE
expectation MAE
global-null lift
oracle-comparator gap
```

Primary guardrails:

```text
forbidden feature count = 0
teacher-self feature count = 0
oracle matrix feature count = 0
validation-label model-selection count = 0
test-label model-selection count = 0
protocol-valid passed = true
catalog physicality audit present for catalog-mechanism replay
```

## Discovery Artifact Bundle

The first Stage 3 implementation should write one reviewable artifact tree:

```text
outputs/PHYC_STAGE3_discovery/
  config.yaml
  visible_feature_schema.json
  visible_feature_matrix.json
  visible_features.npy
  sampled_visible_features.npy
  forbidden_feature_audit.json
  operation_context_public_audit.json
  split_manifest.json
  probe_schedule_manifest.json
  observability_ceiling.json
  oracle_alias_classes.json
  learned_assignments.npy
  learned_assignment_summary.json
  learned_prototypes.json
  prototype_generation_metrics.json
  predicted_assignment_metrics.json
  oracle_assignment_comparator_metrics.json
  global_null_metrics.json
  mean_only_baseline_metrics.json
  assignment_source_audit.json
  heldout_protocol.json
  leakage_audit.json
  assignment_shuffle_metrics.json
  shuffled_assignment_metrics_summary.json
  shuffle_runs.json
  feature_scramble_metrics.json
  scrambled_feature_metrics_summary.json
  feature_scramble_runs.json
  context_shuffle_metrics.json
  context_shuffled_metrics_summary.json
  context_shuffle_runs.json
  k_stress_plan.json
  k_stress_results.json
  k_stress_summary.json
  learned_assignments_by_k.npz
  merge_prune_plan.json
  merge_map.json
  postmerge_metrics.json
  postmerge_assignments.npy
  evaluator_only_label_metrics.json
  quotient_metrics.json
  controls.json
  seed_stability.json
  summary.md
```

Evaluator-only files may contain labels, channels, PTMs, Kraus matrices, and
oracle prototypes for audit and scoring. Learner-input files must contain only
approved visible observations and derived visible features.

Implementation rule: downstream Stage 3 stages consume this bundle through the
shared `scope_static.mechanism_discovery.artifacts` module. Public Stage 3 run
functions are exported from `scope_static.mechanism_discovery`. Stage 3B/3C/3D must not
rebuild learner-visible feature matrices from `oracle_mechanisms.json`, and
must load evaluator-only labels only after fitting or for evaluator-only
ceiling/comparator audits.

## Acceptance Rule

Stage 3 passes only when the accepted discovery model:

- uses no direct mechanism-label supervision;
- consumes only the learner-visible observation surface;
- recovers latent assignments or reports the remaining quotient aliases;
- generates heldout visible observations better than null baselines;
- follows the declared assignment-unit and K-selection protocols;
- passes leakage and protocol audits;
- is validated under the declared batch/context protocol.

A perfect synthetic result may report ARI/NMI/BA/min recall equal to `1.0`.
Do not force exact labels if the visible surface only supports a quotient
alias class.

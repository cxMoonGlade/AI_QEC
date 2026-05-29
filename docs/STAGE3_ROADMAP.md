# Stage 3 Roadmap: Mechanism-Structure Discovery

Stage 3 tests whether SCOPE-Discovery can recover latent mechanism structure,
assignments, and prototypes from learner-visible observations without direct
mechanism-label supervision.

Stage 2 validated the physical mechanism catalog and the no-leakage visible
recovery protocol. Stage 3 now removes direct mechanism-label supervision and
tests whether SCOPE-Discovery can recover latent mechanism structure,
assignments, and prototypes from the same learner-visible observation surface.

## Core Question

```text
Can learner-visible probe observations recover the mechanism structure itself?
```

The Stage 3 learner should infer latent assignments and prototypes. Mechanism
IDs, physical-family labels, exact channels, exact PTMs, and teacher-self
features are evaluator-only.

## Starting Surface

Stage 3 starts from the Layer 3b/3c visible surface:

- Z/X-only probe measurements;
- X-prepared states for phase/coherence observability;
- no Y-basis preparation;
- no Y-basis measurement;
- multi-context batches for drifted mechanisms such as M13;
- raw time-sequence features retained before derived summaries.

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

- latent assignment matrix `S[j, k]` or `Pi[j, k]`;
- learned visible prototypes;
- cluster/quotient alias classes when exact labels are not observable;
- heldout visible-generation model;
- evaluator-only ARI/NMI/BA/min-recall reports;
- prototype quality metrics;
- no-leakage and protocol-validity audits.

## Work Packages

### Stage 3A: Dataset And Protocol Freeze

Freeze the learner-visible dataset contract.

Deliverables:

- visible feature schema;
- probe schedule manifest;
- batch/context schema;
- train/validation/test split policy;
- leakage guardrail audit;
- deterministic visible ceiling audit.

Acceptance:

- no forbidden learner fields;
- Stage 2 visible ceiling remains valid;
- multi-context batch protocol is explicit.

### Stage 3B: Unsupervised Assignment Recovery

Train discovery models without mechanism-label supervision.

Candidate heads:

- mixture model on visible time-sequence features;
- prototype clustering with learned covariance;
- contrastive context-consistency objective;
- local-inverse representation clustering;
- quotient-aware assignment hardening.

Acceptance:

- evaluator-only ARI/NMI reported;
- selected model is not chosen by test labels;
- label permutation is handled explicitly;
- failure reports quotient alias classes instead of forcing exact labels.

### Stage 3C: Prototype And Generator Learning

Learn visible prototypes that can generate heldout probe observations.

Metrics:

- Gaussian NLL on visible features;
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

### Stage 3D: Robustness And Ablations

Prove the result is not accidental.

Required controls:

- label-shuffled control;
- context-shuffled control;
- mean-only ablation;
- covariance-only ablation;
- single-context versus multi-context M13 protocol;
- reduced-probe ablation;
- finite-shot sensitivity.

Acceptance:

- accepted result survives seed/fold changes;
- M13 is only expected to be fully recoverable in multi-context mode;
- failures identify observability, optimization, or protocol limits.

### Stage 3E: Scale And External Validation

Extend after the synthetic Stage 3 claim is stable.

Targets:

- larger allM artifacts;
- additional circuit depths and supports;
- Google proxy validation;
- decoder-facing utility tests;
- cross-context transfer audits.

These are not required for the first Stage 3 discovery pass.

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
visible Gaussian NLL
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
test-label model-selection count = 0
protocol-valid passed = true
```

## Acceptance Rule

Stage 3 passes only when the accepted discovery model:

- uses no direct mechanism-label supervision;
- consumes only the learner-visible observation surface;
- recovers latent assignments or reports the remaining quotient aliases;
- generates heldout visible observations better than null baselines;
- passes leakage and protocol audits;
- is validated under the declared batch/context protocol.

A perfect synthetic result may report ARI/NMI/BA/min recall equal to `1.0`.
Do not force exact labels if the visible surface only supports a quotient
alias class.

# Stage 3 Roadmap: Mechanism-Structure Discovery

Stage 3 tests whether SCOPE-Discovery can learn a latent mechanism quotient
from learner-visible observations without direct mechanism-label supervision.
Discovery means learning assignments, prototypes, and observational alias
classes from visible data, not predicting a mechanism label that was provided to
the learner.

Stage 2 is closed as a no-leakage physical-mechanism catalog validation stage:
the system can generate controlled noisy QEC observations from declared
mechanisms, verify teacher/catalog separability, and train Layer 3 learners
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

Operationally, Stage 3 is the "+1" object above the toolbox: Layer 1 generates
teacher-declared noisy QEC observations from a controlled catalog, Layer 3
learns/replays visible noisy observation distributions under no-leakage
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
parameterized and audited to enforce that constraint directly.

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

### Stage 3D: Quotient Evaluation And Robustness

Evaluate quotient recovery with evaluator-only labels and prove the result is
not accidental.

Required controls:

- label-permutation control;
- context-shuffled control;
- feature-scramble control;
- alias stress test;
- family-holdout control;
- mean-only ablation;
- covariance-only ablation;
- single-context versus multi-context M13 protocol;
- reduced-probe ablation;
- finite-shot sensitivity.

Acceptance:

- accepted result survives seed/fold changes;
- M13 is only expected to be fully recoverable in multi-context mode;
- observational aliases are reported as quotient classes, not forced labels;
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
catalog physicality audit present for catalog-mechanism replay
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

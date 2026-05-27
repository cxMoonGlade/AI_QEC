# Teacher and Learner

This note defines **teacher**, **learner**, and **exposure to the learner** for
`scope_static`: a fixed-context DEM/Bernoulli research stack, not a CPTP/GKSL
physical-channel learner.

## Teacher

A **teacher** is the source of reference truth for an experiment.

Implemented forms:

- SCOPE-Static: defines hidden `omega(j)`, teacher logits `lambda_j`, sampled
  faults `e_j ~ Bernoulli(p_j)`, and observations `y = A e mod 2`.
- S2D physical-oracle work: PHYS1/PHYS2 generate physical mechanism cases and
  oracle separability evidence before PHYS3 learner recovery is judged.

Expected properties:

- reproducible and seed-aware.
- explicit about hidden and oracle-only fields.
- usable by evaluators for ARI/NMI, oracle ceilings, and audits.
- not exposed to the learner except in declared oracle or known-orbit baselines.

## Learner

A **learner** is the model or algorithm trained from learner-visible inputs.

Implemented forms:

- Stage 1: fits DEM fault logits `lambda_j`; known-orbit models may use
  supplied `omega(j)` because Stage 1 is the known-orbit setting.
- Stage 2 static discovery: learns `S[j, k]` or `Pi[j, k]` from `A`, `y`, and
  learner-visible features; hidden `omega(j)` is withheld.
- PHYS3: learns from shot bits, probe metadata, visible instruction type,
  visible qubit/edge ids, chain position, and visible-data-derived invariants.

Expected properties:

- no hidden-label leakage.
- selection by validation NLL and visible health checks, not ARI/NMI.
- reports heldout likelihood, calibration, compression accounting, baselines,
  seed-aware summaries, and leakage audits.

## Exposure to the Learner

**Exposure to the learner** means every information path that can affect the
trained learner, not only the final feature matrix.

Included paths:

- feature construction and preprocessing.
- initialization and warm starts.
- training inputs and targets.
- objective terms and regularizers.
- restart, checkpoint, model, feature, and hyperparameter selection.

Allowed learner-visible data:

- `A` and `y`.
- shot bits.
- visible circuit/probe/instruction/location metadata.
- features computed only from visible data.

Forbidden learner exposure:

- hidden `omega(j)`, except declared Stage 1 known-orbit baselines.
- teacher prototype labels.
- oracle physical mechanism labels.
- exact oracle PTM/RZZ-type features.
- hidden-orbit-centered features.
- ARI/NMI or recovery metrics used for model selection.

Rule: hidden or oracle-only data may appear in evaluator artifacts, not in
learner paths. If recovery succeeds without leakage, the declared visible
representation exposes recoverable structure. If oracle separability is strong
but visible recovery is weak, the result is learner-limited or
observability-limited evidence.

# Teacher and Learner

This note defines **teacher**, **learner**, and **exposure to the learner** for
`scope_static`: a fixed-context DEM/Bernoulli research stack, not a CPTP/GKSL
physical-channel learner.

## Core Notation

For SCOPE-Static Stage 1 and Stage 2 discovery, the data model is the
canonicalized DEM/Bernoulli parity model:

```text
e_j ~ Bernoulli(p_j)
y = A e mod 2
p_j = sigmoid(lambda_j)
```

- `M`: number of effective DEM fault mechanisms after duplicate-mask
  canonicalization.
- `B`: number of observation bits, including detector bits and logical
  observable bits.
- `A in F_2^{B x M}`: DEM parity map. Column `j` records which observation
  bits flip when effective DEM fault `j` occurs.
- `e in {0,1}^M`: latent sampled DEM fault vector for one shot.
- `y in {0,1}^B`: observed detector/logical bit vector for one shot.
- `p_j`: Bernoulli probability of effective DEM fault `j`.
- `lambda_j`: Stage 1 fault logit, `logit(p_j)`.
- `omega(j)`: known orbit assignment for fault `j` in known-orbit Stage 1
  baselines.
- `S[j, k]` or `Pi[j, k]`: learned Stage 2 discovery assignment. Do not call
  this matrix `A`; `A` is reserved for the DEM parity map.

For PHYC2/PHYC3 physical-oracle paths, sampled local observation bits are
learner-visible data when declared, but oracle mechanism labels, exact channels,
exact PTMs, and oracle fingerprints remain evaluator-only.

## Teacher

A **teacher** is the source of reference truth for an experiment.

Implemented forms:

- SCOPE-Static: defines hidden `omega(j)`, teacher logits `lambda_j`, sampled
  faults `e_j ~ Bernoulli(p_j)`, and observations `y = A e mod 2`.
- S2D physical-oracle work: PHYS1/PHYS2 generate physical mechanism cases and
  oracle separability evidence before PHYS3 learner recovery is judged.
- PHYC1-full-circuit: the current Stage 2E mainline teacher; samples literal
  full n-qubit CUDA-Q circuits at configured gate depth with mechanism
  channels/readout.
- PHYC2-separability_v2: generates PHYS1-compatible sampled local observations
  from engineered branch-specific response profiles for stress testing
  learner-visible separability.
- PHYC2-Born-local: Stage 2E teacher that generates sampled local observations
  from exact local Born probabilities for CPTP/readout mechanisms.

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
- PHYC2: trains grouped classifiers from sampled observation bits and
  learner-visible probe/instruction metadata to classify mechanism labels.
- PHYC3: consumes PHYC2 grouped predictions and audits whether predicted
  mechanism labels map to close quantum/readout error prototypes.

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

- `A` and `y` for DEM/Bernoulli Stage 1 and Stage 2 static runs.
- shot bits.
- visible circuit/probe/instruction/location metadata.
- features computed only from visible data.
- PHYC2 slot-remapped observation cells, provided sampled response features are
  used and slot-only leakage control remains low.

Forbidden learner exposure:

- hidden `omega(j)`, except declared Stage 1 known-orbit baselines.
- teacher prototype labels.
- oracle physical mechanism labels.
- exact oracle PTM/RZZ-type features.
- hidden-orbit-centered features.
- ARI/NMI or recovery metrics used for model selection.
- observation slot ids if a remap deterministically encodes mechanism identity.

For the current local-observable path, `PHYC2.slot_only_leakage_control` trains
on slot/layout metadata without sampled bits. High slot-only accuracy means the
PHYC2 result is leaking and should not be trusted. The current accepted
`separability_v2` evidence has low slot-only accuracy and is explicitly
classified as an engineered separability stress result, not a Born-local
physical baseline.

Rule: hidden or oracle-only data may appear in evaluator artifacts, not in
learner paths. If recovery succeeds without leakage, the declared visible
representation exposes recoverable structure. If oracle separability is strong
but visible recovery is weak, the result is learner-limited or
observability-limited evidence.

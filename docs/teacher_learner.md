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

For catalog validation paths, sampled observation bits are
learner-visible data when declared. Oracle mechanism labels, exact channels,
exact PTMs, teacher-self signatures, and oracle fingerprints remain
evaluator-only. Teacher may use teacher-internal evidence to ask whether the
teacher can distinguish itself; Learner may not use that evidence as learner
input. `PHYC1/PHYC2/PHYC3` remain legacy artifact aliases.

Physicality boundary: data preparation is the first-class physical-process teacher.
It validates catalog definitions as unitary channels, Kraus channels, or
classical readout assignment matrices before sampling and blocks failed
artifacts with a post-sampling physicality audit. Learner is not yet an
arbitrary CPTP/GKSL channel learner by construction.

## Response-Surface Intuition

See `docs/RESPONSE_SURFACES.md` for the fuller implementation view across the
controlled teacher-learner path and the Google S3 V2 real-data path.

Teacher-learner mechanism recovery should be understood as learning from a
probe- and context-induced visible response surface, not from direct access to a
continuous geometric surface of the quantum circuit itself. The teacher inserts
or declares probes, basis choices, locations, rounds, and public context. These
choices induce sampled detector and logical-observable responses. Under a
reference or no-error condition, those syndrome/observable responses should be
close to a stable baseline distribution; it is useful, but only intuitive, to
think of that baseline as a smooth surface.

An error mechanism perturbs this visible response distribution. The learner sees
the resulting statistical shape across probes, qubits or detectors, time,
basis, and context: marginal rate shifts, spatial and temporal correlations,
logical-observable coupling, drift, and other sampled-observation-derived
features. In the surface picture, those response signatures are the bumps or
depressions on the otherwise smooth baseline. The learner does not observe the
physical mechanism object directly; it observes these visible response
signatures.

For Stage 2 catalog validation, if these signatures are separable on the
declared learner-visible surface, a no-leakage learner can classify the catalog
mechanisms from sampled observations and approved visible features. For Stage 3
discovery, the stricter goal is to learn assignments, prototypes, or a codebook
from the visible surface without mechanism-label supervision, then use
evaluator-only labels only after training to audit recovery. If two mechanisms
induce indistinguishable or near-indistinguishable visible distributions,
`p(y | m_a) ~= p(y | m_b)`, the correct discovery target is an observational
alias or quotient class, not a forced exact-label split.

## Teacher

A **teacher** is the source of reference truth for an experiment.

Implemented forms:

- SCOPE-Static: defines hidden `omega(j)`, teacher logits `lambda_j`, sampled
  faults `e_j ~ Bernoulli(p_j)`, and observations `y = A e mod 2`.
- S2D catalog work: data preparation generates physical mechanism cases,
  teacher audits teacher self-distinguishment, and learner
  judges no-leakage learner recovery plus generated noise/error quality.
- Data-preparation full-circuit: validates local CPTP/POVM mechanism modules, samples
  literal full n-qubit CUDA-Q circuits at configured gate depth with mechanism
  channels/readout, and runs a blocking post-sampling physicality audit.
- separability_v2: generates data-preparation-compatible sampled local observations
  from engineered branch-specific response profiles for stress testing
  learner-visible separability.
- Born-local: generates sampled local observations
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
- PHYS3 legacy local-inverse recovery: learns from shot bits, probe metadata,
  visible instruction type, visible qubit/edge ids, chain position, and
  visible-data-derived invariants.
- Teacher: not a learner-success claim. It audits whether the
  data-preparation teacher can self-distinguish generated mechanisms from
  teacher-internal mechanism evidence.
- Learner: consumes no-leakage learner grouped predictions, not
  teacher-self predictions, and audits whether predicted
  mechanism labels map to close quantum/readout error prototypes and visible
  generated-noise metrics such as NLL and MAE.

If learner replays a predicted catalog mechanism, it inherits the catalog
unitary/Kraus/readout definition. If it replays only empirical visible
distributions, the result is a visible-distribution model, not a proven learned
CPTP channel.

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
- teacher/learner slot-remapped observation cells, provided sampled response
  features are used and slot-only leakage control remains low.

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
sampled-observation learner diagnostic is leaking and should not be trusted as
learner evidence. It does not invalidate teacher by
itself. The current accepted `separability_v2` evidence is explicitly
classified as an engineered separability stress result, not a Born-local
physical baseline.

Stage 2 is closed as a no-leakage physical-mechanism catalog validation stage:
the system can generate controlled noisy QEC observations from declared
mechanisms, verify teacher/catalog separability, and train learner models
that recover and replay learner-visible noisy observation distributions without
oracle leakage. Stage 3 is the next claim boundary: remove direct
mechanism-label supervision and test whether latent mechanism structure can be
inferred from visible observations alone.

Rule: hidden or oracle-only data may appear in evaluator artifacts, not in
learner paths. If recovery succeeds without leakage, the declared visible
representation exposes recoverable structure. If oracle separability is strong
but visible recovery is weak, the result is learner-limited or
observability-limited evidence.

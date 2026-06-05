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
input.

Physicality boundary: Layer1 preprocessing - teacher generator is the
first-class physical-process generator. It validates catalog definitions as
unitary channels, Kraus channels, or classical readout assignment matrices
before sampling and blocks failed artifacts with a post-sampling physicality
audit. The established learner is not yet an arbitrary CPTP/GKSL channel learner
by construction; as of 2026-06 an exact CPTP physical substrate (SCOPE-Twin
Layer 3/4, `scope_static.primitives.diff_cptp_channel` / `diff_circuit_sim`) is
an active, prioritized small-scale build toward the interventional twin (see
`docs/SCOPE_TWIN.md`).


## Response-Surface Intuition

See `docs/RESPONSE_SURFACES.md` for the fuller implementation view across the
controlled catalog/Layer1 preprocessing - teacher generator path and the
Google S3 V2 real-data path.

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
- S2D catalog work: Layer1 preprocessing - teacher generator generates
  physical mechanism cases, Layer 2 teacher self-audit checks
  teacher/catalog self-distinguishment, and Layer 3 learner judges no-leakage
  learner recovery plus generated noise/error quality.
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
- Layer 3 local-inverse recovery: learns from shot bits, probe metadata,
  visible instruction type, visible qubit/edge ids, chain position, and
  visible-data-derived invariants.
- Layer 2 teacher self-audit: not a learner-success claim. It audits whether
  the teacher generator can self-distinguish generated mechanisms from
  teacher-internal mechanism evidence.
- Layer 3 learner: consumes no-leakage learner grouped predictions, not
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

## Current Implementation Map

The codebase currently has several related but distinct teacher/learner paths.
The important distinction is that data preparation generates observations,
`teacher` audits teacher-internal separability, and `learner` or
`mechanism_discovery` consumes learner-visible features.

### Layer1 preprocessing - teacher generator

Main code:

- `scope_static.data_preparation.physical_process.generate_layer1p_teacher_dataset`
- `scope_static.data_preparation.full_circuit_cudaq.generate_full_circuit_cudaq_teacher_dataset`
- `scope_static.primitives.mechanism_catalog`
- CLI wrapper:
  `scope_static.experiments.qec_noise_catalog.data_preparation_teacher`

Algorithm:

1. Build a declared mechanism batch from the catalog and config. The current
   controlled mainline uses Layer1 preprocessing full-circuit contract settings
   and records `MechanismSpec` entries with public context, mechanism name,
   family, location, strength, and oracle-only channel metadata.
2. Run pre-sampling contract checks: mechanism-definition audit, CPTP/POVM
   guardrail, full-circuit-model audit, readout/channel support checks, and
   sampling contract checks.
3. Build CUDA-Q kernels for each circuit and probe context. The kernel contains
   the ideal circuit schedule, active probe operations, and inserted mechanism
   channels/readout processes according to the selected mechanism records.
4. Sample shot counts, convert counts to observation matrices, apply declared
   readout processes where needed, and write checkpointed chunks before
   consolidation.
5. Write the teacher artifacts used by downstream stages:
   `observations.npz`, `oracle_mechanisms.json`, `teacher_config.json`,
   `sampling_audit.json`, `cptp_guardrail_audit.json`,
   `layer1p_teacher_contract.json`, and `acceptance_audit.json`.

This is the first-class controlled Layer1 preprocessing - teacher generator.
The sampled data are learner-visible only through declared observation/probe
surfaces; oracle mechanism metadata remain evaluator-only.

### Local-observable diagnostic teacher

Main code:

- `scope_static.data_preparation.local_observable_teacher.generate_local_observable_teacher_dataset`

Algorithm:

1. Build balanced catalog mechanism records.
2. Evaluate local response probabilities for the selected response model.
   `separability_v2` is an engineered branch-specific stress teacher;
   `born_local` uses exact local Born probabilities for supported local
   mechanisms and is effectively depth one.
3. Sample local observations and write the same broad artifact family as the
   full-circuit path.

This path is useful for observability and separability diagnostics. It is not
the current full-circuit Stage 3/5 physical-generation claim path.

### Layer 2 teacher self-audit

Main code:

- `scope_static.teacher.distinguishment.run_sampled_observation_separability_audit`
- `scope_static.teacher.observation_surface`
- module wrapper:
  `scope_static.experiments.qec_noise_catalog.teacher_distinguishment`

Algorithm:

1. Load teacher-generated records, especially `oracle_mechanisms.json`.
2. Build teacher-internal signatures from declared mechanism channel data,
   parameters, and readout assignment matrices.
3. Run grouped leave-one-circuit-out prototype classification from those
   teacher-internal signatures.
4. Report balanced accuracy, min recall, ARI, and NMI as a teacher/catalog
   self-distinguishability audit.

This is Layer 2. It is deliberately allowed to use teacher-internal evidence
because it asks whether the catalog can distinguish itself. It is not a
learner-success claim and its predictions must not feed learner training or
model selection.

### Layer 3 no-leakage learner

Main code:

- `scope_static.learner.learner_recovery.run_phyc3_no_leakage_learner_recovery`
- `scope_static.learner.zx_visible_probe_suite`
- `scope_static.learner.gaussian_likelihood.run_phyc3c_distributional_gaussian_likelihood_head`
- `scope_static.mechanism_observability`

Algorithm:

1. Load observations and oracle records from a teacher directory.
2. Build learner-visible typed features from shot bits, probe metadata,
   public instruction type, visible qubit or edge ids, chain position, and
   visible-data-derived invariants.
3. Train grouped supervised heads for the local-inverse/catalog recovery
   diagnostic. Labels are evaluator/supervision targets for this closed Stage 2
   contract, not learner-visible input features.
4. Run slot-only leakage controls, scrambled controls, rare-class metrics,
   generated-noise NLL/MAE checks, and channel/readout replay audits.
5. For distributional diagnostics, fit Gaussian likelihood heads on Z/X visible
   feature batches: mean-only, covariance-only, diagonal Gaussian, shared
   covariance LDA, full Gaussian likelihood, and shrinkage QDA.

This is Layer 3. This path closed Stage 2 catalog validation. It is supervised
and no-leakage; it does not satisfy the stricter Stage 3 requirement of
unsupervised latent assignment from frozen visible features.

### Stage 3/5 discovery learner

Main code:

- `scope_static.mechanism_discovery.protocol_freeze.run_stage3a_dataset_protocol_freeze`
- `scope_static.mechanism_discovery.observability_abc_diagnostic.run_stage3_abc_observability_diagnostic`
- `scope_static.mechanism_discovery.discovery_model.run_stage3b1_first_discovery_model`
- `scope_static.mechanism_discovery.overcomplete_merge_prune_audit`
- `scope_static.mechanism_discovery.property_recovery.run_stage5b1_property_recovery`
- CLI wrappers under `scope_static.experiments.stage3` and
  `scope_static.experiments.stage5`

Algorithm:

1. Stage 3A freezes the learner-visible protocol. It builds
   `visible_features.npy`, sampled visible features, probe manifests, grouped
   split manifests, public context schema, operation-context public audit, and
   forbidden-feature audits. It does not train a classifier.
2. Stage 3A.5 and ABC diagnostics ask what the frozen surface can support.
   The ABC diagnostic runs a supervised evaluator-only upper bound, a no-oracle
   VQ/context-residual representation diagnostic, and optional enhanced-probe
   repeats. Targeted diagnostics are set-based; pair-only target groups are not
   valid because they overstate M6/M13 or M22/M23 separability.
3. Stage 3B1 trains a visible-only prototype mixture. It masks the frozen
   feature matrix according to the configured learner input profile, optionally
   applies public-context residualization, standardizes/weights visible
   features, selects `K` by visible validation objective, then fits diagonal
   covariance prototypes and responsibilities `Pi[j, k]`. Mechanism labels are
   loaded only after fit for evaluator metrics, shortcut audits, and bleed
   audits.
4. Stage 3D4/S3D4b may run overcomplete-`K` visible-only merge/prune. The merge
   rule must not read mechanism labels. It may serve as a downstream assignment
   source only when its own visible-only postmerge gate passes.
5. Stage 5B1 fixes S3B1 or postmerge responsibilities and recovers
   context-relative properties. The simple head uses visible residual energy as
   a location score and context-normalized residual magnitude as a strength
   score. The conditional head fits a public context baseline `b(context)`,
   subtracts it, and scores residual location/strength structure. Evaluator
   records are loaded only after the head is fit.

The Stage 3/5 learner is the current mechanism-structure mainline. Raw S3B1 is
diagnostic by itself; claim-bearing generator/effect recovery requires the
Stage 3B1/S3D4b/S5B1 gates and the downstream `claim_gate_audit`.

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

For the local-observable Stage 2 path,
the Layer 2 slot-only leakage control trains on slot/layout metadata without
sampled bits. High slot-only accuracy means the sampled-observation learner
diagnostic is leaking and should not be trusted as learner evidence. It does
not invalidate the teacher by itself. The accepted `separability_v2` evidence
is explicitly classified as an engineered separability stress result, not a
Born-local physical baseline. The current controlled Stage 3/5 route instead
starts from the Layer1 preprocessing - teacher generator medium contract
artifact, then freezes learner-visible features and audits assignment/property
recovery with evaluator-only labels.

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

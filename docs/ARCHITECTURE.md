# Architecture

`scope_static` is a fixed-context QEC research package. Its implemented core is
the DEM/Bernoulli parity model, with synthetic discovery and physical-mechanism
validation layers built around that core.

```text
e_j ~ Bernoulli(p_j)
y = A e mod 2
lambda_j = logit(p_j)
```

`A in F_2^{B x M}` is the DEM parity map, `e in {0,1}^M` is the latent
effective-fault vector, and `y in {0,1}^B` is the observed detector/logical bit
vector.

The public program has a 2+1 surface:

1. generate teacher-declared noisy QEC observations from a controlled physical
   mechanism catalog;
2. learn from the learner-visible observation surface and replay similar
   reproducible visible noisy observation distributions;
3. the "+1" research object: infer the latent mechanism quotient through Stage
   3 mechanism-structure discovery.

The architecture has four implementation surfaces:

1. Stage 1 DEM fault-logit learning.
2. Stage 2 static discovery and physical catalog validation.
3. Layer 1/2/3 physical-mechanism probe, teacher, and learner diagnostics.
4. Stage 3 latent mechanism-structure discovery on the same learner-visible
   surface.

Stage 2 is closed as a no-leakage physical-mechanism catalog validation stage:
the system can generate controlled noisy QEC observations from declared
mechanisms, verify teacher/catalog separability, and train Layer 3 learners
that recover and replay learner-visible noisy observation distributions without
oracle leakage. Stage 3 is the next claim boundary: remove direct
mechanism-label supervision and test whether latent mechanism structure can be
inferred from visible observations alone.

Physicality boundary: Layer 1 mechanisms are catalog definitions implemented as
unitary channels, Kraus channels, or classical readout assignment matrices. The
current learner is not an arbitrary CPTP/GKSL channel learner by construction.

## Package Map

```text
src/scope_static/
  fault_graph.py        DEM fault graph, duplicate-mask canonicalization
  parity_map.py         parity-map utilities
  stim_dem.py           Stim circuit and DEM helpers
  fields.py             local, hard-orbit, soft-orbit, discovery fields
  likelihood.py         exact global/window likelihood and CUDA dispatch
  likelihoods/          likelihood adapters
  windows.py            local-window builders and audits
  training.py           generic fitting loop
  evidence.py           metrics, compression, threshold summaries
  baselines.py          local, DMLE-style, hard-orbit, soft-orbit baselines
  discovery.py          Stage 2 assignment metrics and oracle deltas
  hardening.py          Stage 2 assignment hardening helpers
  identifiability/      passive visible-signature clustering
  multi_env.py          shared-assignment multi-environment models
  local_mechanism.py    local-inverse representation transforms
  google_set1.py        Google Set1 read-only adapter
  google_mechanism.py   Google proxy partitions and local-inverse audits
  physical/             physical mechanism channels, probes, layers, learners
  physical_oracle/      legacy PHYS stack facade
  archive/              historical research-stage modules with wrappers
  experiments/          runnable command entry points
  cuda/                 C++/CUDA exact DEM/window kernels
```

`configs/scope_static/*.yaml` stores reproducible experiment plans. Runners
write artifacts under `outputs/scope_static/` or `outputs/google_static/`.

## Stage 1 DEM Core

Stage 1 learns `lambda_j` over effective DEM fault columns.

```text
Stim or synthetic DEM
-> FaultGraph canonicalization
-> window plan or exact objective
-> FaultLogitField
-> fit_field
-> evidence records
```

Important contracts:

- sparse fault supports are the scalable interface;
- dense parity matrices are compatibility artifacts for small tests;
- duplicate parity masks are canonicalized before learning;
- compression claims require explicit parameter audits;
- local-window likelihood evaluates exact parity likelihood on each window.

Main model families:

```text
local
dmle_qec
hard_orbit
soft_feature_orbit
```

## Stage 2 Static Discovery

Stage 2 withholds the known orbit map and evaluates recovery with
evaluator-only labels.

```text
synthetic teacher with hidden omega(j)
-> sampled observations y
-> learned assignment S[j, k] or Pi[j, k]
-> evaluator-only ARI/NMI
```

Tracks:

```text
Stage 2A: direct free-assignment DEM quotient recovery
Stage 2C: local-inverse-first discovery
Stage 2D: active local-logit observability and typed physical learners
Stage 2E: physical catalog and visible recovery validation
Stage 2B: Google external predictive validation
```

Stage 2 is now a closed validation record. Stage 3 owns the next unsupervised
latent mechanism-structure claim.

Historical Stage 2 waypoints that are no longer public entry points live under
`scope_static.archive`. Thin wrappers remain at their old paths so historical
configs, tests, and artifact readers keep working.

## Physical Layer Stack

The public layer names replace the old PHYC vocabulary in reports. Legacy
artifact names remain compatible.

```text
Layer 1: Data Preparation (Prep)
  legacy alias: PHYC1

Layer 2: Teacher Self-Distinguishment (Teacher)
  legacy alias: PHYC2

Layer 3: Learner Classification and Noise Generation (Learner)
  legacy alias: PHYC3
```

Layer flow:

```text
mechanism catalog + user-enabled mechanism set
-> Layer 1 probe schedule and sampled noisy observations
-> Layer 2 teacher/catalog self-distinguishability
-> Layer 3 no-leakage learner recovery
-> Layer 3 generated noisy-data quality
```

Layer 2 may use teacher-internal mechanism evidence because its role is teacher
self-distinguishability. Layer 3 may consume only learner-visible probe
observations and declared visible metadata.

Layer 1 emits `cptp_guardrail_audit.json` to check complete-positivity
representation class, declared channel dimension, unitary unitarity, Kraus
trace preservation, readout stochasticity, and parameter validity for every
enabled mechanism record.

## Physical Modules

Core physical modules:

```text
physical/mechanism_catalog.py             M0-M34 mechanism records
physical/channels.py                      synthetic channel/readout objects
physical/ptm.py                           PTM and fingerprint utilities
physical/phyc1_contract.py                Layer 1 contract structures
physical/teacher.py                       teacher facade and mechanism plans
physical/full_circuit_cudaq_teacher.py    full-circuit CUDA-Q teacher
physical/local_observable_teacher.py      scalable local-observable teacher
physical/layers.py                        public Layer 1/2/3 metadata
```

Layer 2 and Layer 3 modules:

```text
physical/sampled_observation_separability.py     Layer 2 teacher audit
physical/phyc3_no_leakage_learner_recovery.py    Layer 3a old-surface learner
physical/phyc3b_zx_visible_probe_suite.py        Layer 3b Z/X visible repair
physical/phyc3c_gaussian_likelihood.py           Layer 3c Gaussian head
physical/phyc3c_validation.py                    Layer 3c validation audits
physical/sampled_quantum_error_quality.py        Layer 3 quality metrics
physical/phyc3_canonical_acceptance.py           canonical Layer 3 resolver
```

Observability and typed-learner modules:

```text
physical/local_pauli_lindblad.py
physical/generator_space_calibration.py
physical/generator_invariant_calibration.py
physical/typed_spam_gate_invariant.py
physical/m1_gate_calibration.py
physical/local_inverse.py
physical_oracle/stack.py
```

Archived physical research modules:

```text
archive/physical/stage2_learner_limit/      S2D.6 targeted representation
archive/physical/stage2_rzz_probe_design/   S2D.7/S2D.8 RZZ probe attempts
archive/physical/stage2_born_local_gate/    S2E.1 Born-local gate audit
```

## Layer 3 Canonical Path

The canonical Layer 3 path is deliberately decomposed:

```text
PHYC2_teacher_self_only_v4
PHYC3a_old_surface_no_leakage_learner_recovery
PHYC3b_ZX_visible_alias_breaking_probe_suite
PHYC3c_distributional_gaussian_likelihood_head
PHYC3_canonical_quality_acceptance
```

`PHYC3_canonical_quality_acceptance` is the legacy artifact name for the Layer 3
canonical resolver. It does not train a new learner. It accepts PHYC3c
multi-context predictions only after Layer 2, Layer 3b, Layer 3c, and protocol
validation pass.

The resolver rejects:

- Layer 2 teacher-self predictions;
- legacy Layer 2 grouped predictions;
- Layer 3a old-surface baseline predictions as the canonical source.

Accepted Layer 3 quality reports include classification metrics, incompatible
prediction counts, channel/readout prototype distances, visible Gaussian NLL,
population cross entropy, and visible-feature MAE.

Layer 3 is the accepted supervised/no-leakage learner surface for replaying
similar visible noisy observation distributions. Stage 3 removes direct
mechanism-label supervision and turns the same surface into a latent mechanism
quotient discovery problem.

## Stage 3 Discovery Surface

Stage 3 should use the same learner-visible Z/X observation surface validated
by Layer 3b/3c, but remove direct mechanism-label supervision.

Allowed learner-visible inputs:

- probe preparation label;
- measurement basis label;
- repeat count;
- qubit count;
- empirical probabilities and expectations;
- shot count;
- finite-shot uncertainty estimates;
- derived features computed only from sampled observations.

Forbidden learner inputs:

- true mechanism ID;
- physical-family label;
- teacher self-distinguishment features;
- exact channel, Kraus, or PTM matrices;
- oracle prototype vectors;
- hidden drift parameters or other identity-derived fields.

Evaluator-only labels may be used for ARI/NMI, quotient-class reports, and
post-training audits.

Exact hidden-label recovery should not be forced when two mechanisms induce the
same visible distribution. In that case, the correct Stage 3 output is an
observational alias class:

```text
m_a ~_obs m_b  <=>  p(y | m_a) ~= p(y | m_b)
```

## Google Adapter

The Google Set1 path is read-only external validation. It supports predictive
likelihood, calibration, transfer, and explicitly labelled proxy-partition
diagnostics. It does not provide true physical-mechanism labels.

## Artifact Contract

Serious experiment artifacts should include:

- run config or manifest;
- metrics JSON;
- compact summary markdown;
- label-use or leakage audit when hidden labels or oracle features exist;
- graph/window/compression audits for DEM runs;
- probe/schema/protocol audits for physical-layer runs.

Terminal output is not evidence by itself. The artifact tree is the evidence
object.

## Claim Boundaries

Implemented claims:

- fixed-context DEM/Bernoulli likelihood experiments;
- known-orbit, discovery, and local-inverse comparisons inside that family;
- synthetic oracle ARI/NMI when hidden labels are evaluator-only;
- Layer 1 teacher-declared noisy QEC observation generation from catalog
  unitary/Kraus/readout mechanism definitions;
- physical-mechanism catalog and visible-recovery validation on synthetic
  teachers;
- Google predictive validation with proxy labels only when explicitly labelled.

Not claimed:

- real-hardware ground-truth mechanism recovery;
- arbitrary learned CPTP/GST/GKSL channel generation by construction;
- learned full noisy-circuit Born-rule likelihood from hardware data;
- complete SCOPE-Twin physical generation;
- decoder utility, cross-context generalization, or drift prediction as
  completed axes.

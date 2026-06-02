# Visible Response Surfaces

This note explains how SCOPE uses learner-visible response surfaces in the
controlled teacher-learner catalog path and in the Google S3 V2 real-data path.
It is a conceptual and implementation bridge: the "surface" is not a direct
geometric surface of the quantum circuit. It is the visible distribution induced
by probes, public context, sampled detector bits, and logical-observable bits.

## Core Intuition

A teacher or real-data context defines a set of probes, basis choices, locations,
rounds, detector regions, and public context fields. Those choices induce sampled
detector and logical-observable responses. Under a reference or no-error
condition, those responses should be close to a stable baseline distribution. It
is useful, but only intuitive, to imagine that baseline as a smooth surface.

An error mechanism perturbs this visible response distribution. The learner sees
the resulting statistical shape across probes, qubits or detectors, time, basis,
and context:

- marginal detector-rate shifts;
- spatial and temporal correlations;
- logical-observable coupling;
- stability, drift, and shotblock variance;
- branch-specific readout, prep/reset, and gate-process response features.

In the surface picture, those response signatures are bumps or depressions on
the otherwise smooth baseline. The learner does not observe the physical
mechanism object directly. It observes visible response signatures.

If two mechanisms induce indistinguishable or near-indistinguishable visible
distributions,

```text
p(y | m_a) ~= p(y | m_b),
```

the correct discovery target is an observational alias or quotient class, not a
forced exact-label split.

## Controlled Teacher-Learner Surface

The controlled catalog path can actively declare mechanisms and probes. Its
pipeline is:

```text
mechanism catalog
  -> probe schedule / context
  -> sampled observations
  -> learner-visible feature surface
  -> classifier / prototype / assignment model
  -> evaluator-only mechanism audit
```

Data preparation writes the controlled teacher artifacts:

```text
oracle_mechanisms.json
observations.npz
active_probe_manifest.json
sampling_audit.json
cptp_guardrail_audit.json
```

`oracle_mechanisms.json` contains evaluator-only mechanism truth such as
`oracle_label`. `observations.npz` is the sampled visible response tensor,
typically shaped like:

```text
[num_probes, shots, num_observation_slots]
```

The active probe manifest records visible probe metadata: basis choices, RZZ
tomography prep and measurement roles, edge parity, detector/qubit support, and
circuit-depth metadata. It is explicitly not an oracle-label, teacher-channel,
or exact-PTM feature source.

For the full-circuit CUDA-Q teacher, non-readout mechanisms are inserted as
unitary or Kraus channels in the circuit/noise model, then sampled. Readout
mechanisms are applied after sampling by flipping readout bits according to the
declared readout assignment matrix.

For the local-observable teacher, the system samples local response profiles for
mechanism records and probe contexts. In allM stress runs, observation-slot
remapping avoids destructive overwrite when multiple local mechanisms would
otherwise share the same probe/qubit response cell.

## Controlled Surface Features

The learner consumes sampled observations and approved visible metadata. It does
not consume exact channels, PTMs, Kraus matrices, teacher-self signatures,
oracle fingerprints, or mechanism labels as input features.

The current learner-visible feature construction includes two important blocks.

First, local Pauli/Lindblad observability reconstructs local response summaries
from sampled observations and probe metadata. It estimates PTM-like response
blocks and generator-coordinate features from visible response data. These are
learner-visible response summaries, not exact oracle PTMs.

Second, the typed SPAM/gate invariant feature builder converts each mechanism
record into feature spaces such as:

```text
flat_raw_generator_or_local_inverse
flat_invariants_only
flat_raw_plus_invariants
typed_gate_readout_prep_invariant_learner
within_branch_scrambled_control
cross_branch_scrambled_control
```

The primary typed feature block includes visible instruction/location features,
single-qubit response features, local-observable response features,
shot-reconstructed PTM proxies, pair correlations, sampled tomography features,
readout features, prep/reset features, and confidence features.

The visible branch rule is public and instruction-based:

```text
measure -> readout_branch
reset   -> prep_reset_branch
other   -> gate_process_branch
```

It does not use row-level oracle labels for branch assignment.

## Controlled Classification And Discovery

Stage 2 / PHYC3 is supervised catalog validation. The mechanism label may be
used as a training target and evaluator label, but not as an input feature. The
main question is:

```text
Can sampled observations classify the declared catalog mechanism without hidden
or oracle-feature leakage?
```

The learner trains grouped heads such as a typed linear head, typed prototype
head, and typed Mahalanobis prototype head. Grouping by `circuit_id` prevents
the same circuit group from leaking across train/test splits.

Controls test whether the model learned response shape rather than metadata
leakage:

```text
slot_only_leakage_control
within_branch_scrambled_control
cross_branch_scrambled_control
```

If the real typed features beat scrambled controls and slot-only accuracy stays
low, the evidence supports no-leakage mechanism classification from the visible
response surface.

Stage 3 is stricter. It freezes a Stage-3A learner-visible matrix:

```text
visible_features.npy
sampled_visible_features.npy
visible_feature_schema.json
visible_feature_matrix.json
split_manifest.json
forbidden_feature_audit.json
```

Then visible-only baselines and discovery models fit assignments, prototypes, or
codebooks from the frozen feature matrix. Mechanism and quotient labels are used
only after fitting to report evaluator-only ARI/NMI, balanced accuracy, minimum
recall, and alias/quotient audits.

So the controlled distinction is:

```text
Stage 2: visible response shape -> supervised mechanism classification
Stage 3: visible response shape -> unsupervised assignment/prototype/codebook
         -> evaluator-only mechanism or quotient audit
```

## Google S3 V2 Surface

The Google path has no controlled mechanism labels and cannot insert new
counterfactual mechanisms. It starts from real public Google observation data:

```text
real Google experiment context
  -> detection_events + obs_flips_actual
  -> public syndrome-response signatures
  -> frozen visible_features.npy
```

The active command chain is:

```bash
scope-google-s3-visible-cache-v2 --config configs/scope_static/google_s3_visible_cache_v2.yaml
scope-google-s3-visible-aggregate-v2 --config configs/scope_static/google_s3_visible_aggregate_v2.yaml
scope-google-s3-visible-adapter-v2 --config configs/scope_static/google_s3_visible_adapter_v2.yaml
```

The cache stage reads each selected Google context and stores public precompute
state:

```text
detection_events
obs_flips_actual
detector coordinates
boundary detectors
logical-support detectors
round-band memberships
region-family memberships
shotblock partitions
source-file hashes for reproducibility
```

Source paths and hashes are protocol metadata. They are not learner-visible
feature columns.

The aggregate stage slices each cached context by public round band and detector
region:

```text
round_band:
  early / mid / late

region_family:
  boundary_adjacent
  bulk
  logical_support_neighborhood
  interior_chain
  full_patch
```

For each `(context, round_band, region_family)` unit, it selects:

```text
selected_detectors = round_detectors intersect region_detectors
```

and computes one public syndrome-response signature row.

The adapter stage merges replicas by public signature key and writes a
Stage-3A-shaped freeze. The assignment unit is:

```text
google_public_syndrome_response_signature
```

A row's public fields may include dataset name, basis, distance, rounds,
round-band, region family, and patch geometry class. These fields define the
public unit of the visible response surface; they are not hidden mechanism
labels.

## Google Feature Blocks

The Google V2 surface currently uses a 66-dimensional visible feature schema
with these blocks:

```text
raw marginal
spatial correlation
temporal correlation
logical coupling
stability / shotblock variance
public geometry
```

The row builder starts from:

```text
detectors   = observations[:, :detector_count]
observables = observations[:, detector_count : detector_count + observable_count]
```

It then computes selected-detector rates, nearest-neighbor covariance and
correlation, adjacent-round temporal covariance and correlation, detector/logical
coupling, shotblock stability, and public geometry summaries.

The learner-visible matrix does not expose context IDs, sample IDs, leaf paths,
decoder correctness targets, catalog labels, hidden mechanism labels, teacher
channels, Kraus matrices, PTMs, oracle prototypes, or other forbidden fields.

The current Google V2 freeze has:

```text
decision: google_s3_visible_surface_v2_passed
visible_features.npy shape: [347, 66]
assignment_unit: google_public_syndrome_response_signature
forbidden_feature_audit: passed
forbidden_feature_count: 0
contains_evaluator_labels: false
contains_oracle_fields: false
```

The current precompute chain reports:

```text
cache decision: google_s3_visible_cache_v2_passed
cache contexts: 24
cache shots: 786432
aggregate decision: google_s3_visible_aggregate_cache_v2_passed
aggregate units: 347
aggregate feature_count: 66
```

The cache and aggregate stages support worker parallelism. Current configs use
`num_workers: 8` and write block-level timing fields into the cache/aggregate
manifests.

## What Google Learns And Does Not Learn

Because Google provides no ground-truth mechanism partition, the Google learner
does not solve:

```text
Which true physical M* mechanism generated this row?
```

The valid Google question is:

```text
Do public syndrome-response signatures contain compressible, replayable, or
transferable visible structure?
```

Therefore Google Stage 3/S4 evidence is scored as visible replay and transfer
against controls:

```text
global / mean-only null
assignment shuffle
feature scramble
public-stratified null
train-on-Google-only
random-codebook transfer
frozen-source-codebook transfer
```

The claim boundary is:

```text
no-oracle replay of public raw syndrome-response structure
```

not:

```text
true Google physical mechanism recovery
Google M* label recovery
```

## Controlled Vs Google Surface

| Property | Controlled teacher-learner | Google S3 V2 |
| --- | --- | --- |
| Mechanisms | Declared catalog mechanisms exist | No true mechanism labels are available |
| Probes | Chosen by the teacher protocol | Fixed by public Google experiment contexts |
| Observations | Generated by controlled teacher sampling | Read from real detection events and observable flips |
| Labels | Evaluator-only, and sometimes supervised targets in Stage 2 | Absent for true physical mechanisms |
| Surface row | Mechanism-condition or frozen visible assignment unit | Public syndrome-response signature |
| Main learner claim | No-leakage classification/replay, then discovery quotient | No-oracle visible replay/transfer |
| Failure mode | Observability aliasing or learner limitation | Surface mismatch, domain shift, or non-transfer of source prototypes |

The same "surface" intuition applies to both paths: visible response
distributions can contain statistically meaningful shapes. The interpretation is
different. In controlled teacher-learner runs, those shapes can be audited
against known catalog mechanisms. In Google runs, those shapes can only be
audited as public visible replay or transfer structure unless a separate,
credible ground-truth mechanism partition is introduced.

## S4.6 Google-Unit Source Surface

S4.6 constructs a controlled source surface at the Google public signature unit:

```text
controlled catalog observations
  -> design-split Google native visible modes
  -> evaluator-only catalog-family mixtures
  -> synthetic_public_syndrome_response_signature rows
  -> Stage-3A-compatible source freeze
```

The learner-visible S4.6 matrix contains only visible syndrome-response features.
Mixture weights, dominant family, mode tags, and exact catalog summaries are
evaluator-only manifests.

S4.6 may use Google visible rows only through the declared design split for mode
construction. Validation rows train calibrator/replay heads. Heldout rows score
final transfer and gap closure.

S4.6 robustness closeout checks whether the mechanism-mixture source structure
beats public-context-only, random-mixture, target-mean/std, visible dMLE-style
marginal MLE, random-codebook, global-null, and source-structure ablation
controls. It still claims visible replay/source-transfer only, not true Google
physical mechanism recovery.

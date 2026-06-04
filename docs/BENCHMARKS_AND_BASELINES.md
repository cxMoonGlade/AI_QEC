# Benchmark And Baseline Selection

This note defines the next benchmark ladder after the current S5 controlled
milestone. It keeps three claims separate:

1. controlled catalog identifiability and effect recovery;
2. Google-shaped visible bridge survival;
3. real Google visible-syndrome replay or decoder utility.

## Current Starting Point

The current controlled milestone is the repaired full-circuit allM/decorrelated
teacher chain:

```text
S3D4b_overcomplete_merge_prune_audit
S5B1b_conditional_property_recovery
```

This benchmark can use evaluator-only controlled catalog labels after fitting
to report BA, min recall, ARI, NMI, context-relative location, and
context-normalized strength/effect. It must not be used to claim Google physical
mechanism recovery.

The current S4 repaired smoke shows that the controlled teacher can be projected
into a Google V2-compatible 66-feature visible schema, but S4.0.5 reports
`bridge_surface_projection_aliasing`. That means exact 35-way catalog survival
is not currently the right S4 target on the compressed Google-shaped surface
unless the bridge surface is strengthened.

## Benchmark Ladder

### B0 Controlled Full-Circuit Catalog

Use for identifiability, no-oracle assignment, and S5 property recovery.

Required controls:

- global-null and mean-only visible replay;
- assignment shuffle;
- feature scramble;
- context shuffle;
- K-stress undercomplete/exact/overcomplete;
- S3D4b visible-only merge/prune leakage audit;
- S5B1b evaluator-only assignment-quality gate.

Acceptance target: controlled S3D4b/S5B1b stays green across repeats without
using mechanism labels, location, or strength for fit or model selection.

### B1 Synthetic Google-Shaped Bridge

Use before neural S4 work. This benchmark asks whether the public Google V2
schema preserves a useful controlled mechanism or alias quotient.

Required controls:

- S4.0 schema and forbidden-feature audit;
- S4.0.5 source visible ceiling;
- alias class map and collapse matrix;
- linear probe, kNN probe, and no-oracle Stage 3B1 probe;
- global-null, random-codebook, feature-scramble, assignment-shuffle, and
  public-context controls.

Acceptance target: either exact/near-exact 35-way structure survives, or a
declared alias quotient survives strongly enough to be a legitimate S4 target.
If S4.0.5 reports `bridge_surface_projection_aliasing`, do not start neural
training as the main claim.

### B2 Google V2 Public Visible Surface

Use for real-data no-oracle replay of public syndrome-response structure. It has
no hidden physical mechanism labels.

Required controls:

- global/mean-only;
- assignment shuffle;
- feature scramble;
- context shuffle where public context is used;
- public-stratified null;
- visible-surface dMLE-style independent marginal MLE;
- random-codebook and train-on-Google-only controls for transfer claims.

Primary scoring profiles:

- `raw_target_only`;
- `block_normalized`;
- `full_target` only as a compatibility diagnostic.

Acceptance target: heldout raw visible replay beats the strong public-field-only
controls with paired bootstrap or split-repeat stability, without claiming
mechanism recovery.

### B3 Published Surface-Code Hardware Datasets

Use after B1/B2 are stable to compare against recognized public hardware
benchmarks. The first candidates are Google's published surface-code datasets:

- 2023 Sycamore distance-3/distance-5 data for "Suppressing quantum errors by
  scaling a surface code logical qubit";
- 2024/2025 Willow distance-3/distance-5/distance-7 and repetition-code data
  for "Quantum error correction below the surface code threshold".

Use these for public syndrome-response replay and later decoder-facing
benchmarks. They are not hidden mechanism-label datasets.

### B4 Stim/Sinter Synthetic Surface-Code Benchmarks

Use Stim/Sinter when we need reproducible synthetic scale, controlled code
distance, rounds, and noise model sweeps. These should be paired with PyMatching
or correlated-MWPM-style decoders so decoder utility can be compared against a
standard QEC baseline rather than only against internal replay scores.

### B5 Decoder Utility Benchmarks

Use only after visible replay and bridge survival are stable. Decoder utility
must report logical error per round or per cycle, not only representation replay.

Baseline order:

- PyMatching/MWPM as the standard fast matching baseline;
- correlated MWPM or belief-matching when correlated error priors are available;
- tensor-network or approximate maximum-likelihood decoders as slow upper
  baselines where feasible;
- AlphaQubit-style neural decoding only as a later deep benchmark, not as the
  first fix for visible-surface or teacher-payload failures.

## Model Escalation Rule

Use the existing A/B/C decision rule before changing learner capacity:

- A: supervised oracle upper-bound from frozen visible features to controlled
  labels. If A fails, repair visible probes, teacher payload, or the bridge
  projection.
- B: no-oracle representation diagnostics such as VQ, contrastive,
  reconstruction, or context consistency. If A passes but B/S3B1 fails, model
  capacity or objective mismatch is plausible.
- C: enhanced-probe or repaired-payload upper bound. If C improves A/B/S3B1, the
  main cause was visible geometry or payload, not a lack of deep learning.

## Source Notes

Sources checked on 2026-06-04:

- Google Quantum AI, "Suppressing quantum errors by scaling a surface code
  logical qubit", Nature 2023:
  https://www.nature.com/articles/s41586-022-05434-1
- Data for "Suppressing quantum errors by scaling a surface code logical
  qubit", Zenodo:
  https://zenodo.org/records/6804040
- Google Quantum AI and Collaborators, "Quantum error correction below the
  surface code threshold", Nature 2024/2025:
  https://www.nature.com/articles/s41586-024-08449-y
- Data for "Quantum error correction below the surface code threshold", Zenodo:
  https://zenodo.org/records/13273331
- Stim: a fast stabilizer circuit simulator:
  https://arxiv.org/abs/2103.02202
- PyMatching documentation:
  https://pymatching.readthedocs.io/en/latest/index.html
- "Learning high-accuracy error decoding for quantum processors", Nature 2024:
  https://www.nature.com/articles/s41586-024-08148-8

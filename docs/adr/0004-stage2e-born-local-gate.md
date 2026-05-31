# ADR 0004: Stage 2E Born-Local Gate Before Stage 3

## Status

Superseded by `0005-stage2e-full-circuit-cudaq-mainline.md`.

## Context

The local-observable Torch CUDA path produced strong historical
`separability_v2` evidence: PHYC2-balanced, PHYC2-weighted, slot-only leakage
control, no-remap ablation, 74-qubit/depth-200 scalability smoke, and PHYC3
mechanism-to-error prototype quality on the engineered sampled-observation
teacher.

Current public terminology separates these claims more sharply: teacher
validation means teacher self-distinguishment, while learner means
no-leakage learner recovery plus quantum/readout and visible-generation quality.
Older PHYC3 artifacts
should be rechecked for a
learner prediction source before being cited as no-leakage learner evidence.

However, `separability_v2` is intentionally engineered for learner-visible
mechanism separability. It uses branch-specific response profiles and
correlation overlays rather than exact local Born probabilities from a
CPTP/readout channel. Treating it as a physical baseline would overstate the
claim.

## Decision

Stage 2 adds a late gate:

```text
Stage 2E: Born-local physical baseline
```

This decision is historical. ADR 0005 supersedes it by making full-circuit
CUDA-Q PHYC1 the Stage 2E mainline and acceptance surface.

Use the names precisely:

```text
PHYC2-separability_v2:
  engineered separability stress teacher

PHYC2-Born-local:
  physically and mathematically correct local baseline

PHYC3-Born-local:
  no-leakage learner recovery and error-quality audit for the Born-local
  diagnostic
```

Historically, Stage 3 was blocked on PHYC2-Born-local and the corresponding
PHYC3-Born-local quality audit. ADR 0005 superseded that gate. The current
pre-release boundary is: Stage 2 is closed as a controlled-catalog/no-leakage
recovery validation stage; Stage 3 removes direct mechanism-label supervision
and tests whether latent mechanism structure can be inferred from visible
observations alone.

## Consequences

- Current `separability_v2` results remain valid as synthetic separability and
  scalability evidence.
- The physical baseline claim requires a new local teacher:

  ```text
  local probe state -> CPTP/readout mechanism -> exact local Born probability
  -> GPU sampled observation bits
  ```

- The Born-local teacher must not use mechanism-label response templates,
  artificial response-code margins, or post-sampling pair-correlation overlays.
- Small Born-local cases should be validated against direct density-matrix math
  and CUDA-Q local circuits before promoting allM PHYC1/PHYC2/PHYC3 evidence.

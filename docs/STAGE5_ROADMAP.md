# Stage 5 Roadmap: Context-Relative Mechanism Effects

Stage 5 starts after visible mechanism/family structure has been recovered. Its
object is not only which mechanism family is present, but also where the effect
usually acts inside its context and how strongly it deforms the visible response
surface.

## Core Question

```text
Given a recovered mechanism/family assignment, can we audit its
context-relative location and context-normalized visible strength?
```

## Claim Boundary

S5 is an evaluator/audit layer over frozen visible artifacts. It may use
controlled-catalog evaluator records to name families, exact `M*` mechanisms,
oracle parameters, and provenance locations after fitting. These fields must not
enter learner training or model selection.

S5 may claim context-relative visible effect recovery on controlled source data.
It must not claim true Google physical mechanism recovery, Google `M*` label
recovery, Born-rule physical generation, or CPTP/GKSL parameter learning.

## Current Artifact

The current implementation is emitted by Stage 3C because it consumes the same
inputs: Stage 3A frozen `visible_features.npy`, Stage 3B.1 responsibilities, and
controlled-catalog evaluator records.

Primary artifact:

- `s5_context_relative_mechanism_effect_audit.json`

Compatibility alias:

- `soft_family_strength_location_audit.json`

The artifact reports:

- `per_family`: context-relative location and visible strength by recovered
  family bucket;
- `per_exact_mechanism`: the same audit by exact controlled-catalog `M*` label;
- `context_relative_action_locations`: location ranks/fractions and qubit
  center/span inside each context;
- `visible_strength.context_relative_reference`: primary strength after
  subtracting context-local visible means and standardizing by context-local
  scale;
- `visible_strength.global_reference`: comparison-only global mean/scale view;
- `oracle_parameter_strength`: evaluator-only numeric summaries of teacher
  parameters, for controlled-source interpretation only.

## Minimum Pass

- S5 artifact is evaluator-only or explicitly skipped in no-oracle mode.
- Family classification NMI/ARI/BA/min-recall are `1.0` on controlled
  teacher-learner fixtures before S5 effect claims are cited.
- Location uses the `context_relative` reference frame.
- Strength uses `context_relative_reference` as the primary frame.
- Absolute IDs appear only as provenance counts.
- The artifact does not claim physical parameter recovery.

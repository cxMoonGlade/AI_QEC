# Stage 5 Roadmap: Context-Relative Mechanism Effects

Stage 5 starts after visible mechanism/family structure has been recovered. Its
object is not only which mechanism family is present, but also where the effect
is likely to appear inside its context and how strongly it deforms the visible
response surface.

## Core Question

```text
Given a recovered mechanism/family assignment, can we audit its
context-conditioned error likelihood and context-normalized visible strength?
```

## Claim Boundary

S5 is an evaluator/audit layer over frozen visible artifacts. It may use
controlled-catalog evaluator records to name families, public `F*` flat labels,
public `M*` non-flat labels, legacy catalog IDs, oracle parameters, and
provenance locations after fitting. These fields must not enter learner
training or model selection.

S5 may claim context-relative visible effect recovery on controlled source data.
Here "location" means context-conditioned likelihood/support over
context-relative cells: in a given public/probe context, where is this visible
effect likely to appear? It is not an absolute physical-coordinate recovery
claim. S5 must not claim true Google physical mechanism recovery, Google public
F/M label recovery, Google legacy catalog-ID recovery, Born-rule physical
generation, or CPTP/GKSL parameter learning.

Context is the discovery lens, not the latent property being balanced. Controlled
S5 teachers used for location/strength recovery should decouple `context_id`,
context-relative location, and mechanism strength. In current medium-hard
fixtures this is done with `balanced_strength_variant_strategy:
decorrelated_latin`, so each mechanism still receives the required strength
variants without making strength a monotone surrogate for context order or
relative location sweep. Context-balanced views may remain diagnostics, but they
are not the real-data discovery assumption.

## Current Artifact

The current implementation is emitted by Stage 3C because it consumes the same
inputs: Stage 3A frozen `visible_features.npy`, Stage 3B.1 responsibilities, and
controlled-catalog evaluator records.

Primary artifact:

- `s5_context_relative_mechanism_effect_audit.json`
- `mechanism_taxonomy_contract_audit.json`
- `mechanism_dimension_recovery_audit.json`

Compatibility alias:

- `soft_family_strength_location_audit.json`

The artifact reports predicted-vs-oracle effect recovery:

- `per_family`: predicted effect, oracle effect, and recovery metrics by
  recovered family bucket;
- `per_exact_mechanism`: the same audit by legacy controlled-catalog ID, with
  public F/M labels reported for interpretation;
- `effect_recovery_metrics`: aggregate pass/fail and maximum scalar error;
- `contract_typed_recovery_metrics`: acceptance-oriented summary using
  public `F*` exact recovery, family recovery, public `M*` dimension recovery,
  and legacy M11/public M6 overlay recovery;
- `mechanism_dimension_recovery_audit`: evaluator-only dimension audit for
  aggregate, mixture, context-conditioned, operation-conditioned, surrogate,
  and overlay targets;
- `context_relative_action_locations`: location ranks/fractions and qubit
  center/span inside each context, kept as the compatibility view;
- `context_likelihood`: primary S5 location view: weighted support/likelihood
  that an effect appears in a context-relative cell conditioned on the
  public/probe context;
- `visible_strength.context_relative_reference`: primary strength after
  subtracting context-local visible means and standardizing by context-local
  scale;
- `visible_strength.global_reference`: comparison-only global mean/scale view;
- `oracle_parameter_strength`: evaluator-only numeric summaries of teacher
  parameters, for controlled-source interpretation only.

## Minimum Pass

- S5 artifact is evaluator-only or explicitly skipped in no-oracle mode.
- Family classification NMI/ARI/BA/min-recall are `1.0` on controlled
  Layer1.P/Stage3 fixtures before S5 effect claims are cited.
- Predicted family/exact-mechanism effects match oracle evaluator effects on
  controlled Layer1.P/Stage3 fixtures.
- The S5 leaf-effect contract fixture must cover every current implementation
  leaf with `leaf_exact_effect_supported=true`, with at least 20
  context/location/strength variants per leaf.
- Controlled teacher variants must keep mechanism strength and
  context-relative location separable from `context_id`; otherwise S5 effect
  recovery can pass by learning a context surrogate rather than a mechanism
  property.
- Non-flat primary targets in `MECHANISM_CONTRACTS` must not be interpreted as
  standalone physical mechanism recovery from exact-label recall alone. They
  require family/dimension audit: axis, direction, branch, mixture, context,
  operation, surrogate, or overlay fields as applicable.
- Surface-conditional flat `F*` targets keep their public flat label but are not
  flat-exact claim gates on the current Z/X-visible surface. Current examples
  are legacy M6/public F2 and legacy M22-M23/public F9-F10; S5 must claim them
  through family/dimension plus context-relative location and strength until a
  stronger probe surface exposes the required drift or axis signature.
- Legacy `M11` / public `M6` is tested as a spectator-crosstalk overlay
  family, not as a flat exact mechanism. The overlay contract must report base
  mechanism, overlay presence, victim/aggressor relative location, coupling
  axis, timing context, and overlay strength.
- The harder learned Layer1.P/Stage3 fixture must include multiple public
  contexts, all five family buckets, public F/M label coverage with
  non-degenerate context-relative location fractions, and non-degenerate
  numeric parameter strengths.
- Location uses the `context_relative` reference frame and has
  `context_conditioned_error_likelihood` semantics.
- Strength uses `context_relative_reference` as the primary frame.
- Absolute IDs appear only as provenance counts.
- The artifact does not claim physical parameter recovery.

Current boundary: the leaf-effect contract fixture verifies S5 recovery when
the implementation-leaf assignment is already correct. The current learned
fixture is the medium Layer1.P allM contract teacher with M11/public M6
spectator-overlay payload serialized into `oracle_mechanisms.json` and checked
by the blocking physicality/protocol-freeze audits. It is not evidence that
every public `M*` label is an atomic flat discovery target. A learned S3B1
all-catalog gate should target public `F*` atomic leaves where allowed and
family/dimension recovery for aggregate, context-conditioned, mixture,
surrogate, and overlay contracts.

## Spectator Overlay Contract

Legacy `M11` / public `M6` is a context-conditioned overlay family:

```text
observed_effect =
  base_mechanism
  + spectator_overlay(victim, aggressor, axis, timing, strength)
```

It is not a standalone physical channel class on the same axis as `M8` or `M7`.
The S5 overlay audit reports:

- `base_mechanism`;
- `spectator_overlay_present`;
- `victim_relative_location`;
- `aggressor_relative_location`;
- `coupling_axis`;
- `timing_context`;
- `overlay_strength`;
- context-relative visible strength and context-likelihood summaries for each
  base-plus-overlay slice.

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

The current claim-bearing implementation is Stage 5B1b conditional property
recovery over a fixed downstream assignment source. It consumes Stage 3A frozen
`visible_features.npy`, Stage 3A.5 observability artifacts, Stage 3B1 diagnostic
responsibilities, and the visible-only S3D4b postmerge assignment matrix.
Controlled-catalog evaluator records are loaded only after the assignment source
and property head are fixed.

Current milestone artifact:

```text
outputs/scope_static/s5_medium_hard_allM_contract_teacher_20q_depth20_rzz_active_g20_strength_decorrelated_s1000/
  S3D4b_overcomplete_merge_prune_audit/
  S5B1b_conditional_property_recovery/
```

The S5B1b assignment source is:

```yaml
assignment_source: stage3d4b_postmerge
assignment_path: .../S3D4b_overcomplete_merge_prune_audit/postmerge_assignments.npy
property_head_model: conditional_visible_context_property_head
```

Primary artifact:

- `metrics.json`
- `s5b1_property_recovery_metrics.json`
- `targeted_m6_m13_m18_m27_property_audit.json`
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

Current controlled milestone status:

- S3D4b decision: `stage3d4b_overcomplete_merge_prune_audit_passed`.
- S3D4b claim decision: `stage3d4b_postmerge_claim_gate_passed`.
- S3D4b postmerge exact BA/min-recall/ARI/NMI: `1.0 / 1.0 / 1.0 / 1.0`.
- S5B1b decision: `stage5b1_property_recovery_passed`.
- S5B1b assignment source audit: row-stochastic `stage3d4b_postmerge`,
  `uses_mechanism_labels=false`, `uses_oracle_location_or_strength=false`.
- S5B1b assignment quality gate: `claim_allowed=true`.
- S5B1b family BA/min-recall/ARI/NMI: `1.0 / 1.0 / 1.0 / 1.0`.

This milestone means the controlled full-circuit teacher-learner chain can
recover the controlled catalog mechanism structure and its context-relative
location/strength effects from the declared learner-visible surface. It does
not mean true Google physical mechanism recovery, Google public F/M recovery,
or learned CPTP/GKSL parameter recovery.

## Minimum Pass

- S5 artifact is evaluator-only or explicitly skipped in no-oracle mode.
- Family classification NMI/ARI/BA/min-recall are `1.0` on controlled
  Layer1 preprocessing/Stage 3 fixtures before S5 effect claims are cited.
- Predicted family/exact-mechanism effects match oracle evaluator effects on
  controlled Layer1 preprocessing/Stage 3 fixtures.
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
  stronger probe surface exposes the required drift or axis signature. Their
  targeted diagnostics must be set-based with at least three labels, never
  pair-only M6/M13 or M22/M23 tasks.
- Legacy `M11` / public `M6` is tested as a spectator-crosstalk overlay
  family, not as a flat exact mechanism. The overlay contract must report base
  mechanism, overlay presence, victim/aggressor relative location, coupling
  axis, timing context, and overlay strength.
- The harder learned Layer1 preprocessing/Stage 3 fixture must include multiple public
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
fixture is the medium Layer1 preprocessing - teacher generator allM contract
artifact with M11/public M6 spectator-overlay payload serialized into
`oracle_mechanisms.json` and checked by the blocking physicality/protocol-freeze
audits. It is not evidence that
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

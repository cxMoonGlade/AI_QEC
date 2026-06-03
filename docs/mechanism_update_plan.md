# Mechanism Label Update Plan

Status date: 2026-06-02.

## Current Label Contract

Controlled-catalog labels now have two layers:

- `legacy_catalog_id`: implementation-stable legacy IDs `M0`-`M34`.
- `public_label`: semantic labels used for current mechanism claims.

Public labels use two namespaces:

- `F0`-`Fn`: flat atomic visible-effect targets.
- `M0`-`Mn`: non-flat mechanism/family targets.

The compatibility rule is strict: old artifacts may keep `mechanism_id` and
`oracle_label` as legacy IDs, but new teacher records and audits should also
write `legacy_catalog_id`, `public_label`, and `label_namespace`.

## Implemented So Far

- `MECHANISM_CONTRACTS` defines flat versus non-flat contract roles.
- `mechanism_taxonomy_contract_audit.json` reports the F/M public label mapping.
- `mechanism_dimension_recovery_audit.json` audits non-flat targets
  evaluator-only.
- S3C/S5 acceptance uses contract-typed recovery:
  - public `F*` exact recovery for flat targets;
  - family/dimension recovery for public `M*` targets;
  - overlay recovery for legacy M11 / public M6.
- S5 leaf-effect fixtures cover current implementation leaves with
  context/location/strength variants.

## Current Evidence State

The existing full-circuit allM chain had:

```text
S3A:  passed
S3A5: passed
S3B1: passed
S3C/S5: failed under the new contract gate
```

The failure was localized to old legacy M11 records. Those records still looked
like a flat `{"epsilon": ...}` mechanism and did not include spectator overlay
dimensions. This is not a family-recovery or flat-target failure; it means the
teacher artifact predates the new overlay contract.

## Required Teacher Refresh

Before regenerating teacher evidence:

1. Keep legacy IDs stable for compatibility.
2. Emit `public_label` and `label_namespace` for every mechanism record.
3. For public `F*` targets, generate at least 20 context/location/strength
   variants per flat target.
4. For public `M*` targets, generate at least 20 variants per target with the
   target-specific dimensions populated.
5. For legacy M11 / public M6, populate:
   - `base_mechanism`;
   - `spectator_overlay_present`;
   - `victim_relative_location`;
   - `aggressor_relative_location`;
   - `coupling_axis`;
   - `timing_context`;
   - `strength` or `spectator_strength`;
   - `claims_standalone_flat_mechanism: false`.

## Rerun Order

Run the controlled teacher path before Google/S4:

```text
S3A freeze
S3A5 ceiling
S3B1 discovery
S3C/S5 audit
```

Check:

- family NMI/ARI;
- public `F*` exact recovery;
- public `M*` dimension recovery;
- context-relative location error;
- context-normalized strength error;
- legacy M11 / public M6 overlay recovery.

## Failure Taxonomy

```text
surface ceiling fail:
  probe/surface is insufficient; repair the surface or quotient.

family pass, dimension fail:
  S5/audit or visible surface is missing a required dimension.

dimension pass, legacy exact-ID fail:
  may be a valid quotient; not necessarily a bug.

legacy M11 flat fail:
  not a failure by itself; inspect overlay recovery for public M6.

family fail:
  S3B1 learner/feature/normalization failed.
```

## S4/S4.6 Boundary

Only after S3/S5 contract evidence is stable should S4/S4.6 source-teacher work
be rerun. The Google question is not:

```text
Does Google recover legacy M11?
```

The correct questions are:

```text
Does Google-shaped/source transfer preserve family-plus-dimension structure?
Does it preserve spectator-overlay-like signatures?
Does it improve visible replay beyond controls?
```

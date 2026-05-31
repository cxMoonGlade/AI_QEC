# ADR 0003: Catalog Pipeline Facade

## Status

Accepted.

## Context

S2D catalog-validation experiments repeatedly run PHYS1 teacher generation, PHYS2 oracle separability, and PHYS3 local-inverse recovery, but the ordering, artifact paths, verdicts, and timing audits were duplicated across experiment runners.

## Decision

Introduce `scope_static.catalog_pipeline` as a facade package for the
Catalog Pipeline. Current implementation modules live under
`data_preparation`, `teacher`, `learner`, and
`mechanism_observability`; low-level physical-process support lives under
`backend`.

## Consequences

- Experiment runners use one pipeline interface for teacher generation, teacher self-distinguishability, and learner recovery.
- Responsibility-named packages are the stable implementation adapters.
- Data-preparation internals can be decomposed behind the facade without
  changing caller-facing pipeline semantics.

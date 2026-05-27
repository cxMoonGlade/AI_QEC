# ADR 0003: Physical Oracle Stack Facade

## Status

Accepted.

## Context

S2D physical-oracle experiments repeatedly run PHYS1 teacher generation, PHYS2 oracle separability, and PHYS3 local-inverse recovery, but the ordering, artifact paths, verdicts, and timing audits were duplicated across experiment runners.

## Decision

Introduce `scope_static.physical_oracle` as a facade package for the Physical Oracle Stack while leaving the existing PHYS1/PHYS2/PHYS3 implementations in `scope_static.physical`.

## Consequences

- Experiment runners use one stack interface for teacher generation, teacher self-distinguishability, and learner recovery.
- The existing physical modules remain stable implementation adapters for this refactor slice.
- PHYS1 internals can be decomposed later behind the facade without changing caller-facing stack semantics.

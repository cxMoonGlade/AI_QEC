# carrier

## Ownership

This package owns backend-neutral record containers and folds, reusable channel algebra, exact and
research carrier implementations, and the fused within-cycle execution boundary.

`mps/` is a deliberately non-scientific child: it contains bounded execution mechanics for the
restricted frontend routes, not a registered Carrier and not a state-, Record-, or LER-faithfulness
claim. Its child README is binding for that local boundary.

## Boundary

Carrier code propagates a specified process and emits state, trajectory, or record results. It does
not infer a device model, expose evaluator-only process truth, or turn a local diagnostic into a
full-record certificate. Backend-specific contracts remain in their child-package READMEs.

## Entry points

The public record boundary is `RecordBatch`, `PackedShotBatch`, `pack_raw_syndrome_shots`, `s_to_det`,
and `det_to_s`. `FusedWithinCycleSampler` owns the fused execution route, while
`assemble_substep_channel` is owned by `joint_lindbladian.py`.

## Acceptance

See `tests/test_record_batch_units.py`, `tests/test_carrier_record_fold.py`,
`tests/test_joint_lindbladian.py`, and `tests/test_fused_within_cycle_sampler.py`. The complete owner
map is `docs/service_status.json` and generated `docs/CODE_MAP.md`.

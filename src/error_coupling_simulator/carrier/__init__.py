"""Forward-propagation substrate for the specified-noise simulator.

The Axis-1 assembler exponentiates one same-substep joint Lindbladian. Carrier
implementations expose the common immutable record boundary from this package.
"""

from .record_fold import det_to_s, s_to_det
from .records import (
    PACKED_DETECTOR_INITIAL_PRIOR,
    PACKED_SHOT_SCHEMA,
    PACKED_SYNDROME_LAYOUT,
    PackedShotBatch,
    RecordBatch,
    pack_raw_syndrome_shots,
    unpack_raw_syndrome_shots,
)
from .within_cycle import (
    FusedWithinCycleSampler,
    PRECISION_POLICY,
    RUN_PURPOSES,
    RunSpec,
    WithinCycleMarshalled,
    c128_evidence_record_batch,
    cast_within_cycle_precision,
    package_build_identity,
    require_c128_evidence_header,
)

__all__ = [
    "PackedShotBatch",
    "PACKED_DETECTOR_INITIAL_PRIOR",
    "PACKED_SHOT_SCHEMA",
    "PACKED_SYNDROME_LAYOUT",
    "FusedWithinCycleSampler",
    "PRECISION_POLICY",
    "RecordBatch",
    "RUN_PURPOSES",
    "RunSpec",
    "WithinCycleMarshalled",
    "c128_evidence_record_batch",
    "cast_within_cycle_precision",
    "det_to_s",
    "package_build_identity",
    "pack_raw_syndrome_shots",
    "require_c128_evidence_header",
    "s_to_det",
    "unpack_raw_syndrome_shots",
]

"""carrier — forward propagation substrate for the coupling-error simulator.

- ``joint_lindbladian`` (<- qec_twin.forward.joint_lindbladian): the Axis-1 within-substep
  joint-Lindbladian assembler (ONE ``expm`` over ΣH + ΣD[c]; Choi→Kraus; the G2 HEADLINE substrate).

MIGRATION (P2): the canonical home is here; ``qec_twin.forward.joint_lindbladian`` is now a thin
re-export SHIM so all existing importers keep working unchanged until they are migrated to the
package path. GPU-only (cuda, complex128).
"""

from .record_fold import det_to_s, s_to_det
from .records import (
    PackedShotBatch,
    RecordBatch,
    ShotSet,
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
    "FusedWithinCycleSampler",
    "PRECISION_POLICY",
    "RecordBatch",
    "RUN_PURPOSES",
    "RunSpec",
    "ShotSet",
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

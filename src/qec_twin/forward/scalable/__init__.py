"""forward/scalable -- the C1 composed-carrier arm (ADR 0008 C3 seam test).

See this module's README.md: per-window exact CPTP factors + the declared seam
composition rule. The >15-qubit bulk engine (DEM/HMM bulk, dMLE-TN baseline)
remains future ADR 0008 work; nothing here claims beyond the seam-test scale.
"""

from qec_twin.forward.scalable.composed import (
    CarrierManifest,
    ComposedCarrier,
    SlotState,
    StripContext,
    StripLaw,
    StripObservations,
    StripSpec,
    WindowLaw,
    composed_strip_law,
    fit_composed_carrier,
    reduced_qubit_state,
    seam_conditional_reduction,
    split_strip_record,
    strip_cross_entropy,
    strip_entropy,
    strip_joint_kl,
    strip_law_total_variation,
    strip_observations_from_records,
    window_joint_codes,
)
from qec_twin.forward.scalable.marginals import r_det_lag, t3_triple
from qec_twin.forward.scalable.pins import (
    CarrierErrorAccounting,
    EpsLogRecord,
    SeamResidualRecord,
    fixed_point_pin,
    nonpositive_pin,
    normalization_pin,
    pauli_ablation_pin,
    seam_reduction_tp_pin,
    unital_diagonal_pin,
    zero_seam_exactness_pin,
)

__all__ = [
    "CarrierManifest",
    "ComposedCarrier",
    "SlotState",
    "StripContext",
    "StripLaw",
    "StripObservations",
    "StripSpec",
    "WindowLaw",
    "composed_strip_law",
    "fit_composed_carrier",
    "reduced_qubit_state",
    "seam_conditional_reduction",
    "split_strip_record",
    "strip_cross_entropy",
    "strip_entropy",
    "strip_joint_kl",
    "strip_law_total_variation",
    "strip_observations_from_records",
    "window_joint_codes",
    "r_det_lag",
    "t3_triple",
    "CarrierErrorAccounting",
    "EpsLogRecord",
    "SeamResidualRecord",
    "fixed_point_pin",
    "nonpositive_pin",
    "normalization_pin",
    "pauli_ablation_pin",
    "seam_reduction_tp_pin",
    "unital_diagonal_pin",
    "zero_seam_exactness_pin",
]

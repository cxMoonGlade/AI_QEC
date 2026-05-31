"""Backend support for quantum-process mechanisms and probe construction.

This package contains low-level channel, PTM, density-simulation, CPTP/POVM
audit, preflight, and probe-catalog helpers. Stage workflows live in
``data_preparation``, ``teacher``, ``learner``,
``mechanism_observability``, and ``mechanism_discovery``.
"""

from .channels import (
    MechanismSpec,
    amplitude_damping_kraus,
    custom_non_pauli_kraus,
    mechanism_channel,
    pauli_stochastic_kraus,
    readout_bias_matrix,
    rx_unitary,
    ry_unitary,
    rz_unitary,
    rzz_unitary,
)
from .cptp_guardrail import (
    audit_mechanism_physicality,
    build_cptp_guardrail_audit,
    build_cptp_guardrail_audit_from_records,
)
from .density_sim import apply_kraus, measurement_probabilities_z
from .mechanism_catalog import IMPLEMENTED_MECHANISM_IDS, MECHANISM_NAMES, NAMED_MECHANISM_SETS
from .preflight import audit_cudaq_backend, write_backend_audit
from .probe_contract import (
    FULL_CIRCUIT_TEACHER_MODEL,
    LOCAL_OBSERVABLE_TEACHER_MODEL,
    PHYC1_LEGACY_STAGE_NAME,
    PHYC1_STAGE_NAME,
    normalize_phyc1_teacher_model,
)
from .ptm import (
    channel_fingerprint,
    pauli_basis,
    probe_response_fingerprint,
    ptm_from_kraus,
    ptm_from_unitary,
    rzz_ptm_block_audit,
    rzz_type_feature_dict,
    rzz_type_feature_names,
    rzz_type_feature_vector,
)

__all__ = [
    "FULL_CIRCUIT_TEACHER_MODEL",
    "IMPLEMENTED_MECHANISM_IDS",
    "LOCAL_OBSERVABLE_TEACHER_MODEL",
    "MECHANISM_NAMES",
    "MechanismSpec",
    "NAMED_MECHANISM_SETS",
    "PHYC1_LEGACY_STAGE_NAME",
    "PHYC1_STAGE_NAME",
    "amplitude_damping_kraus",
    "apply_kraus",
    "audit_cudaq_backend",
    "audit_mechanism_physicality",
    "build_cptp_guardrail_audit",
    "build_cptp_guardrail_audit_from_records",
    "channel_fingerprint",
    "custom_non_pauli_kraus",
    "measurement_probabilities_z",
    "mechanism_channel",
    "normalize_phyc1_teacher_model",
    "pauli_basis",
    "pauli_stochastic_kraus",
    "probe_response_fingerprint",
    "ptm_from_kraus",
    "ptm_from_unitary",
    "readout_bias_matrix",
    "rx_unitary",
    "ry_unitary",
    "rz_unitary",
    "rzz_ptm_block_audit",
    "rzz_type_feature_dict",
    "rzz_type_feature_names",
    "rzz_type_feature_vector",
    "rzz_unitary",
    "write_backend_audit",
]

"""Physical-channel helpers for S2D synthetic oracle experiments."""

from .channels import (
    MechanismSpec,
    amplitude_damping_kraus,
    custom_non_pauli_kraus,
    mechanism_channel,
    pauli_stochastic_kraus,
    readout_bias_matrix,
    rx_unitary,
    rz_unitary,
    rzz_unitary,
)
from .density_sim import apply_kraus, measurement_probabilities_z
from .preflight import audit_cudaq_backend, write_backend_audit
from .ptm import (
    channel_fingerprint,
    pauli_basis,
    probe_response_fingerprint,
    ptm_from_kraus,
    ptm_from_unitary,
    rzz_type_feature_dict,
    rzz_type_feature_names,
    rzz_type_feature_vector,
    rzz_ptm_block_audit,
)

__all__ = [
    "MechanismSpec",
    "amplitude_damping_kraus",
    "apply_kraus",
    "audit_cudaq_backend",
    "channel_fingerprint",
    "custom_non_pauli_kraus",
    "measurement_probabilities_z",
    "mechanism_channel",
    "pauli_basis",
    "pauli_stochastic_kraus",
    "probe_response_fingerprint",
    "ptm_from_kraus",
    "ptm_from_unitary",
    "readout_bias_matrix",
    "rx_unitary",
    "rz_unitary",
    "rzz_type_feature_dict",
    "rzz_type_feature_names",
    "rzz_type_feature_vector",
    "rzz_ptm_block_audit",
    "rzz_unitary",
    "write_backend_audit",
]

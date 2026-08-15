"""Clifford-augmented all-qubit PEPS engineering prototype."""

from .algebra import (
    TableauGeneratorBasis,
    TableauPauliDecomposition,
    decompose_pauli_in_tableau,
    expand_local_unitary_to_paulis,
)
from .frame import (
    SDIM_INSPECTED_COMMIT,
    SDIM_SUPPORTED_VERSION,
    CliffordFrame,
    FrameBackendStatus,
    FrameBackendUnavailable,
    SdimCliffordFrame,
    StimCliffordFrame,
    sdim_backend_status,
)
from .residual import (
    CDTYPE,
    DenseResidual,
    QuimbPepsResidual,
    ResidualState,
    ResidualStateError,
    ResidualUpdate,
    ZeroProbabilityBranch,
)
from .state import (
    CAPEPSState,
    CliffordRefactor,
    CoherentUpdate,
    MeasurementBranch,
    MeasurementEvent,
    PauliExpectation,
)

__all__ = [
    "CAPEPSState",
    "CDTYPE",
    "CliffordRefactor",
    "CliffordFrame",
    "CoherentUpdate",
    "DenseResidual",
    "FrameBackendStatus",
    "FrameBackendUnavailable",
    "MeasurementBranch",
    "MeasurementEvent",
    "PauliExpectation",
    "QuimbPepsResidual",
    "ResidualState",
    "ResidualStateError",
    "ResidualUpdate",
    "SDIM_INSPECTED_COMMIT",
    "SDIM_SUPPORTED_VERSION",
    "SdimCliffordFrame",
    "StimCliffordFrame",
    "TableauGeneratorBasis",
    "TableauPauliDecomposition",
    "ZeroProbabilityBranch",
    "decompose_pauli_in_tableau",
    "expand_local_unitary_to_paulis",
    "sdim_backend_status",
]

"""Certify controlled noise-process records against independent formal anchors.

See ``README.md``. ``certify_noise_process`` is the neutral public spelling;
``certify_teacher`` remains available for compatibility with historical callers.
"""

from .facade import certify_noise_process, certify_teacher
from .channel_diagnostics import pauli_basis, ptm_from_kraus, ptm_from_unitary
from .types import (
    Anchor,
    AnchorValue,
    Capability,
    CertReport,
    CliffordSliceable,
    Control,
    ControlledNoiseProcess,
    DMReplayable,
    EpistemicClass,
    Exactness,
    Feasibility,
    LedgerRow,
    Regime,
    Statistic,
    Verdict,
)

__all__ = [
    "Anchor",
    "AnchorValue",
    "Capability",
    "CertReport",
    "CliffordSliceable",
    "Control",
    "ControlledNoiseProcess",
    "DMReplayable",
    "EpistemicClass",
    "Exactness",
    "Feasibility",
    "LedgerRow",
    "Regime",
    "Statistic",
    "Verdict",
    "certify_noise_process",
    "certify_teacher",
    "pauli_basis",
    "ptm_from_kraus",
    "ptm_from_unitary",
]

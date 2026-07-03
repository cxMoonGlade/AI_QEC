"""certify — certify a controlled teacher's records against independent ground-truth anchors.

See ``README.md``. Step 1 exposes the interface (the value types + the ``Anchor`` port); the core
(route → controls-first → score → ledger), the concrete DM / stim / closed-form anchors, and the
``certify_teacher`` facade arrive in later steps.
"""

from .facade import certify_teacher
from .types import (
    Anchor,
    AnchorValue,
    Capability,
    CertReport,
    CliffordSliceable,
    Control,
    ControlledTeacher,
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
    "ControlledTeacher",
    "DMReplayable",
    "EpistemicClass",
    "Exactness",
    "Feasibility",
    "LedgerRow",
    "Regime",
    "Statistic",
    "Verdict",
]

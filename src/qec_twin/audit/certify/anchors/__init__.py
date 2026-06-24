"""Ground-truth anchor adapters + the negative controls — each WRAPS a validated wheel.

- ``dm_oracle.DMOracleAnchor`` — the exact density-matrix route (``forward.exact.qutrit_dm``).
- ``stim_clifford.StimCliffordAnchor`` — the implementation-independent Clifford-slice wiring check
  (wraps stim; graduates the ~11 scattered ``_stim_mpp_oracle`` copies into one home).
- ``controls.CorruptStabControl`` / ``ShuffleControl`` — the first-class negative controls.

These are the production anchors/controls. The in-memory anchor used to test the core lives in
``tests/`` (a known-law fixture, never a real ground-truth route).
"""

from qec_twin.audit.certify.anchors.closed_form import ClosedFormAnchor
from qec_twin.audit.certify.anchors.controls import CorruptStabControl, ShuffleControl
from qec_twin.audit.certify.anchors.dm_oracle import DMOracleAnchor
from qec_twin.audit.certify.anchors.stim_clifford import StimCliffordAnchor

__all__ = ["DMOracleAnchor", "StimCliffordAnchor", "ClosedFormAnchor",
           "CorruptStabControl", "ShuffleControl"]

"""SHIM package — moved to ``error_coupling_simulator.certify`` (MIGRATION P4, 2026-07-03).

The teacher-certification seam (record schema, Anchor/Control independent-GT ports, ControlledTeacher
protocol, certify_cells scoring) now lives in the standalone package. This shim keeps every importer
of ``qec_twin.audit.certify`` working: it re-exports the package's top-level names AND aliases every
submodule in ``sys.modules`` so ``import qec_twin.audit.certify.core`` /
``from qec_twin.audit.certify.types import ControlledTeacher`` / ``...anchors.dm_oracle`` all resolve.
"""
import sys as _sys

from error_coupling_simulator import certify as _pkg
from error_coupling_simulator.certify import core, types, facade, anchors
from error_coupling_simulator.certify.anchors import (
    closed_form,
    controls,
    dm_oracle,
    stim_clifford,
)

globals().update({_k: _v for _k, _v in vars(_pkg).items() if not _k.startswith("__")})
for _name, _mod in [
    ("core", core), ("types", types), ("facade", facade), ("anchors", anchors),
    ("anchors.closed_form", closed_form), ("anchors.controls", controls),
    ("anchors.dm_oracle", dm_oracle), ("anchors.stim_clifford", stim_clifford),
]:
    _sys.modules[__name__ + "." + _name] = _mod
del _sys, _pkg

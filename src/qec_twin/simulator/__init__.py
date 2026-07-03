"""SHIM package — moved to ``error_coupling_simulator.frontend`` (MIGRATION P5, 2026-07-03).

The user-facing simulator frontend (CircuitIR / CodeSpec / compiler / schedule / carrier-execution
paths / record emitters) now lives in the standalone package. This shim keeps every importer of
``qec_twin.simulator`` working: it re-exports the package's public API AND aliases every frontend
submodule in ``sys.modules`` so ``from qec_twin.simulator import CircuitBuilder`` /
``from qec_twin.simulator.axis1_record_evidence import ...`` / ``import qec_twin.simulator.stim_io``
all resolve. Edit the canonical modules in the package; migrate call sites + remove this shim in P7.
"""
import importlib as _importlib
import pkgutil as _pkgutil
import sys as _sys

from error_coupling_simulator import frontend as _pkg

# 1) re-export the public API (frontend/__init__ mirrors the old simulator/__init__).
globals().update({_k: _v for _k, _v in vars(_pkg).items() if not _k.startswith("__")})

# 2) alias EVERY frontend submodule so both ``from qec_twin.simulator.<sub> import X`` and
#    ``import qec_twin.simulator.<sub>`` resolve to the moved module (old submodule files deleted).
for _info in _pkgutil.iter_modules(_pkg.__path__):
    _mod = _importlib.import_module("error_coupling_simulator.frontend." + _info.name)
    _sys.modules[__name__ + "." + _info.name] = _mod
    globals()[_info.name] = _mod

del _importlib, _pkgutil, _sys, _pkg

"""SHIM — canonical XZZX parser moved to the active simulator frontend."""

import importlib as _importlib
import sys as _sys

_module = _importlib.import_module(
    "error_coupling_simulator.frontend.xzzx_parser")
_sys.modules[__name__] = _module

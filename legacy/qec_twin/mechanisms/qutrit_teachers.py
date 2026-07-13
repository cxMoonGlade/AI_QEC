"""SHIM — moved to ``error_coupling_simulator.mechanisms.qutrit_teachers`` (MIGRATION P3, 2026-07-03).

Thin re-export so every importer of ``qec_twin.mechanisms.qutrit_teachers`` keeps working unchanged.
"""
from error_coupling_simulator.mechanisms import qutrit_teachers as _m

globals().update({_k: _v for _k, _v in vars(_m).items() if not _k.startswith("__")})
del _m

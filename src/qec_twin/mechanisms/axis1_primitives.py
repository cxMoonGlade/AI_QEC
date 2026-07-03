"""SHIM — moved to ``error_coupling_simulator.mechanisms.axis1_primitives`` (MIGRATION P3, 2026-07-03).

Thin re-export so every importer of ``qec_twin.mechanisms.axis1_primitives`` keeps working unchanged.
"""
from error_coupling_simulator.mechanisms import axis1_primitives as _m

globals().update({_k: _v for _k, _v in vars(_m).items() if not _k.startswith("__")})
del _m

"""SHIM — moved to ``error_coupling_simulator.source.process`` (MIGRATION P3, 2026-07-03).

Thin re-export so every importer of ``qec_twin.mechanisms.source_process`` keeps working unchanged.
"""
from error_coupling_simulator.source import process as _m

globals().update({_k: _v for _k, _v in vars(_m).items() if not _k.startswith("__")})
del _m

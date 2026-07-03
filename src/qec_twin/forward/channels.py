"""SHIM — moved to ``error_coupling_simulator.carrier.channels`` (MIGRATION P2, 2026-07-03).

Thin re-export so every importer of ``qec_twin.forward.channels`` keeps working unchanged.
Edit the canonical module in the package; migrate call sites + remove this shim in P7.
"""
from error_coupling_simulator.carrier import channels as _m

globals().update({_k: _v for _k, _v in vars(_m).items() if not _k.startswith("__")})
del _m

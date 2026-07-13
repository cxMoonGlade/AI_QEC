"""SHIM — moved to ``error_coupling_simulator.carrier.exact.circuit_sim`` (MIGRATION P2, 2026-07-03).

Thin re-export so every importer of ``qec_twin.forward.exact.circuit_sim`` keeps working unchanged.
Edit the canonical module in the package; migrate call sites + remove this shim in P7.
"""
from error_coupling_simulator.carrier.exact import circuit_sim as _m

globals().update({_k: _v for _k, _v in vars(_m).items() if not _k.startswith("__")})
del _m

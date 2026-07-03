"""SHIM — moved to ``error_coupling_simulator.carrier.accel`` (MIGRATION P2, 2026-07-03).

Thin re-export so every importer of ``qec_twin.forward.accel`` keeps working unchanged. The CUDA
kernel sources moved with it to ``error_coupling_simulator/carrier/kernels/`` (accel loads them from
its own sibling dir, so the move keeps the paths correct). Edit the canonical module in the package.
"""
from error_coupling_simulator.carrier import accel as _m

globals().update({_k: _v for _k, _v in vars(_m).items() if not _k.startswith("__")})
del _m

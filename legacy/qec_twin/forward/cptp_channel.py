"""SHIM — moved to ``error_coupling_simulator.carrier.cptp_channel`` (MIGRATION P2, 2026-07-03).

Thin re-export so every importer of ``qec_twin.forward.cptp_channel`` keeps working unchanged.
Edit the canonical module in the package; migrate call sites + remove this shim in P7.
"""
from error_coupling_simulator.carrier import cptp_channel as _m

globals().update({_k: _v for _k, _v in vars(_m).items() if not _k.startswith("__")})
del _m

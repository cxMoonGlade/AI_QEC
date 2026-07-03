"""SHIM — moved to ``error_coupling_simulator.mechanisms.teachers`` (MIGRATION P5, 2026-07-03).

Thin re-export so every importer of ``qec_twin.mechanisms.teachers`` (audit/bands, gating, validity,
calibration/nll, forward/scalable + the twin tests) keeps working unchanged. These Kraus/field
builders are physics-core; the package owns them and the learner depends via this shim. Edit the
canonical module in the package; migrate call sites + remove this shim in P7.
"""
from error_coupling_simulator.mechanisms import teachers as _m

globals().update({_k: _v for _k, _v in vars(_m).items() if not _k.startswith("__")})
del _m

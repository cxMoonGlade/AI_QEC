"""SHIM — moved to ``error_coupling_simulator.noise_processes.coupled_cycle`` (MIGRATION P5, 2026-07-03).

Thin re-export so every importer of ``qec_twin.mechanisms.coupled_teachers`` (the g4 record gate,
test_coupled_cycle_teacher, gate config) keeps working unchanged. Edit the canonical module in the
package; migrate call sites + remove this shim in P7.
"""
from error_coupling_simulator.noise_processes import coupled_cycle as _m

globals().update({_k: _v for _k, _v in vars(_m).items() if not _k.startswith("__")})
del _m

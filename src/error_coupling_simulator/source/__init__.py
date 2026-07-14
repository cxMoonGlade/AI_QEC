"""Axis-2 memoryful sources consumed by specified noise processes.

- ``process`` (<- qec_twin.mechanisms.source_process; P3): the productionized cross-cycle source
  timelines (RTNSource / OneOverFDriftSource / PhaseBurstSource / TemporalStormSPPSource +
  SourceTimeline + matched-marginal baselines).
- ``coupling`` (<- qec_twin.mechanisms.source_coupling; P3): ``Theta(z_t)`` fan-out (one source draw
  -> many mechanism params); ``process`` builds on it.

The lower-level wedge machinery (nm_source/divisibility/wedge = RTN/1f samplers + RHP/BLP
CP-divisibility + coherence-wedge observable) was REMOVED in the 2026-07-03 screening — nothing in the
simulator wires it yet; it stays frozen in ``outputs/teacher_prereg/`` and is re-homed only when a
declared quantum-bath process consumes it (keep the package lean = only what the simulator needs).
"""

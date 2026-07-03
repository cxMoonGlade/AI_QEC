"""source — Axis-2 memory-ful noise sources + the coherence-wedge observable.

- ``nonmarkovian`` (<- outputs/teacher_prereg/nm_source.py): RTN / 1/f / shared-bath samplers with
  exact analytic autocorrelation + Lorentzian PSD; the memory-ful source layer.
- ``divisibility`` (<- nm_divisibility.py): RHP / BLP CP-divisibility (non-Markovianity) detectors —
  the wedge = coherence-revival / CP-divisibility-breaking observable.
- ``wedge`` (<- nm_wedge.py): the coherence-envelope observable harness.
- ``process`` (<- qec_twin.mechanisms.source_process; P3): the PRODUCTIONIZED cross-cycle source
  timelines (RTNSource / OneOverFDriftSource / PhaseBurstSource / TemporalStormSPPSource +
  SourceTimeline + matched-marginal baselines) — the teacher-consumable Axis-2 layer.
- ``coupling`` (<- qec_twin.mechanisms.source_coupling; P3): ``Theta(z_t)`` fan-out (one source draw
  -> many mechanism params); ``process`` builds on it.

Consolidation note (later phase): ``process`` productionizes the lower-level ``nonmarkovian`` math
(RTN/1/f samplers); they coexist here (different API layers) — reconcile into ONE coherent source
API in a later cleanup, do not maintain divergent copies.
"""

"""source — Axis-2 memory-ful noise sources + the coherence-wedge observable.

- ``nonmarkovian`` (<- outputs/teacher_prereg/nm_source.py): RTN / 1/f / shared-bath samplers with
  exact analytic autocorrelation + Lorentzian PSD; the memory-ful source layer.
- ``divisibility`` (<- nm_divisibility.py): RHP / BLP CP-divisibility (non-Markovianity) detectors —
  the wedge = coherence-revival / CP-divisibility-breaking observable.
- ``wedge`` (<- nm_wedge.py): the coherence-envelope observable harness.

Consolidation TODO (later phase): ``qec_twin.mechanisms.source_process`` already productionizes
``nonmarkovian``; reconcile into ONE source layer, do not maintain two.
"""

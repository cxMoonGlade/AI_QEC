"""Noise-mechanism primitives and controlled generative processes.

- ``catalog``: retained M0--M34 dispatch/audit taxonomy for the legacy probe/profile stack;
  it is not the current simulator-construction registry.
- ``axis1_primitives``: current local 2q-window primitive lowering (H_list/c_list inputs for the
  carrier's joint Lindbladian).
- ``qutrit_teachers``: non-Pauli leakage process parameters (WG rates, evaluator-only ``params``).
- ``seam_teachers``: ADR-0008 controlled seam-process fixtures. The historical module names are
  retained for import compatibility; active implementations are package-local.

The Axis-2 source layer (source_process/source_coupling) lives under ``source/`` (process.py,
coupling.py). MIGRATION (P3): these are canonical here; the old ``qec_twin.mechanisms.*`` are shims.
"""

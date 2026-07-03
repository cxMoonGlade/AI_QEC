"""mechanisms — noise-mechanism primitives + controlled teachers (evaluator-only).

- ``catalog`` (<- qec_twin.mechanisms.catalog): mechanism-ID -> CPTP/readout channel defs.
- ``axis1_primitives`` (<- ...): local 2q-window primitive lowering (H_list/c_list inputs for the
  carrier's joint_lindbladian).
- ``qutrit_teachers`` (<- ...): non-Pauli leakage teacher params (WG rates, .params/truth pattern).
- ``seam_teachers`` (<- ...): ADR-0008 seam-test teachers (still imports ``qec_twin.mechanisms.teachers``
  cross-package until teachers.py is moved).

The Axis-2 source layer (source_process/source_coupling) lives under ``source/`` (process.py,
coupling.py). MIGRATION (P3): these are canonical here; the old ``qec_twin.mechanisms.*`` are shims.
"""

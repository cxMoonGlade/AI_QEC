"""carrier.exact — exact density-matrix backend (FEASIBILITY-ONLY, <=~15q).

- ``qutrit_dm``: the QutritDM register (apply_local_op_q,
  apply_channel_2site, leaked-readout POVM).
- ``circuit_sim``: exact circuit / measurement enumeration.

The retained ``qec_twin.forward.exact.{qutrit_dm,circuit_sim}`` import paths are
repository-only outward re-export shims. Circuit/schedule parsing used by the
simulator is owned by ``error_coupling_simulator.frontend``.
"""

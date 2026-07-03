"""carrier.exact — exact density-matrix backend (FEASIBILITY-ONLY, <=~15q).

- ``qutrit_dm`` (<- qec_twin.forward.exact.qutrit_dm): the QutritDM register (apply_local_op_q,
  apply_channel_2site, leaked-readout POVM).
- ``circuit_sim`` (<- qec_twin.forward.exact.circuit_sim): exact circuit / measurement enumeration.

MIGRATION (P2): canonical here; the old ``qec_twin.forward.exact.{qutrit_dm,circuit_sim}`` are
re-export shims. Other ``qec_twin.forward.exact`` modules (rep_code, xzzx_parser, ...) are NOT moved
yet — they land with the frontend/mechanisms phases.
"""

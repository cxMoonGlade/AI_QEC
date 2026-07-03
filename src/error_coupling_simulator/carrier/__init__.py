"""carrier — forward propagation substrate for the coupling-error simulator.

- ``joint_lindbladian`` (<- qec_twin.forward.joint_lindbladian): the Axis-1 within-substep
  joint-Lindbladian assembler (ONE ``expm`` over ΣH + ΣD[c]; Choi→Kraus; the G2 HEADLINE substrate).

MIGRATION (P2): the canonical home is here; ``qec_twin.forward.joint_lindbladian`` is now a thin
re-export SHIM so all existing importers keep working unchanged until they are migrated to the
package path. GPU-only (cuda, complex128).
"""

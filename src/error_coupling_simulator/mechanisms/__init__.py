"""Noise-mechanism primitives and controlled generative processes.

- ``catalog``: retained M0--M34 dispatch/audit taxonomy for the legacy probe/profile stack;
  it is not the current simulator-construction registry.
- ``axis1_primitives``: current local 2q-window primitive lowering (H_list/c_list inputs for the
  carrier's joint Lindbladian).
- ``qutrit_teachers``: non-Pauli leakage process parameters (WG rates, evaluator-only ``params``).
- ``seam_teachers``: ADR-0008 controlled seam-process fixtures. The historical module names are
  retained for import compatibility; active implementations are package-local.
- ``cz_leakage``: QuTiP-derived two-transmon CZ leakage-channel construction from declared
  Hamiltonian/Lindblad parameters. QuTiP is loaded only when this derivation API is requested.

The Axis-2 source layer (source_process/source_coupling) lives under ``source/`` (process.py,
coupling.py). MIGRATION (P3): these are canonical here; the old ``qec_twin.mechanisms.*`` are shims.
"""

from __future__ import annotations

from importlib import import_module


_CZ_LEAKAGE_EXPORTS = frozenset(
    {
        "CZParams",
        "LeakageChannel",
        "TWO_PI",
        "J1_profile",
        "build_cz_channel",
        "build_td_hamiltonian",
        "coupling_H",
        "cz_propagator",
        "cz_propagator_calibrated",
        "cz_superoperator",
        "flux_omega_profile",
        "ghz",
        "interaction_point_omega_flux",
        "ladder_couplings",
        "leaked_out_of_track",
        "mhz",
        "superop_to_truncated_kraus",
        "transmon_H_static",
        "transport_fractions",
    }
)


def __getattr__(name: str):
    """Load the optional QuTiP channel deriver only when its public API is requested."""

    if name in _CZ_LEAKAGE_EXPORTS:
        module = import_module(f"{__name__}.cz_leakage")
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted((*globals(), *_CZ_LEAKAGE_EXPORTS))


__all__ = sorted(_CZ_LEAKAGE_EXPORTS)

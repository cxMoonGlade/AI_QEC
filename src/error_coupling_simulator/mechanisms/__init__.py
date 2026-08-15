"""Specified mechanism primitives used by current simulator processes.

``axis1_primitives`` lowers declared local generators for the joint Lindbladian.
``qutrit_leakage`` owns qutrit exchange/seepage/heating channels, diagnostics, and
noise-process factories. ``cz_leakage`` derives two-transmon CZ leakage channels
from declared Hamiltonian/Lindblad parameters and loads QuTiP only on demand.
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

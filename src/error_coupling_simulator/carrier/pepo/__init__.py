from __future__ import annotations

"""Two-dimensional density-matrix PEPO carrier for a rotated XZZX patch.

Modules have disjoint ownership:

- ``layout``: diamond -> grid transform, frozen-cut site lists, plaquette paths,
  the codestate PEPO builder (:class:`PepoLayout`, :class:`PepoState`,
  :func:`build_codestate_pepo`, :func:`dense_rho`).
- ``dynamics``: single-site superops, the stabilizer-channel TT, NTU truncation,
  ledgers.
- ``sampler``: boundary-MPS norm cache, ``Tr(rho Pi)`` site caps, terminal
  observable reads, and the negativity witness.

Re-exports are LAZY (PEP 562) and per-name, so importing the package — or any one
builder's names — never requires the sibling modules to exist (parallel-build safe).
"""

from importlib import import_module

_EXPORTS = {
    # layout
    "PepoLayout": "layout",
    "PepoState": "layout",
    "build_codestate_pepo": "layout",
    "dense_rho": "layout",
    "fused_bond_name": "layout",
    "fused_phys_name": "layout",
    "site_tag": "layout",
    # dynamics
    "apply_token_stream": "dynamics",
    "apply_postmeasure": "dynamics",
    "stab_channel_tt": "dynamics",
    "StabTT": "dynamics",
    "apply_stab_branch": "dynamics",
    "ntu_truncate": "dynamics",
    "svd_precut_bond": "dynamics",
    "nonselective_round": "dynamics",
    "gap_rank": "dynamics",
    # sampler
    "pepo_trace": "sampler",
    "NormCache": "sampler",
    "norm_cache": "sampler",
    "expect_site_caps": "sampler",
    "stab_expectation": "sampler",
    "terminal_readout_obs": "sampler",
    "terminal_readout_obs_prob": "sampler",
    "s_to_det": "sampler",
    "det_to_s": "sampler",
    "negativity_witness": "sampler",
    "NegativityStats": "sampler",
}

__all__ = sorted(_EXPORTS)


def __getattr__(name: str):
    mod = _EXPORTS.get(name)
    if mod is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return getattr(import_module(f".{mod}", __name__), name)


def __dir__() -> list:
    return sorted(set(globals()) | set(_EXPORTS))

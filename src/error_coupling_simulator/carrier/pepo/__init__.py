from __future__ import annotations

"""carrier.pepo — rung-1 2D density-matrix PEPO carrier for the rotated d x d XZZX patch.

Binding docs: ``docs/nonpauli_teacher/pepo_engine_rung1_contract.md`` (v4.2) under
``docs/nonpauli_teacher/pepo_d5d7_carrier_prereg.md`` (v2.4). Modules (disjoint
ownership, contract s1):

- ``layout`` [A1]: diamond -> grid transform, frozen-cut site lists, plaquette paths,
  the codestate PEPO builder (:class:`PepoLayout`, :class:`PepoState`,
  :func:`build_codestate_pepo`, :func:`dense_rho`).
- ``dynamics`` [A2]: single-site superops, the stabilizer-channel TT, NTU truncation,
  ledgers.
- ``sampler`` [A3]: boundary-MPS norm cache, Tr(rho.Pi) site caps, Born sampling +
  selective update, the C3 negativity witness.

Re-exports are LAZY (PEP 562) and per-name, so importing the package — or any one
builder's names — never requires the sibling modules to exist (parallel-build safe).
"""

from importlib import import_module

_EXPORTS = {
    # layout [A1]
    "PepoLayout": "layout",
    "PepoState": "layout",
    "build_codestate_pepo": "layout",
    "dense_rho": "layout",
    "fused_bond_name": "layout",
    "fused_phys_name": "layout",
    "site_tag": "layout",
    # dynamics [A2]
    "apply_token_stream": "dynamics",
    "apply_postmeasure": "dynamics",
    "stab_channel_tt": "dynamics",
    "StabTT": "dynamics",
    "apply_stab_branch": "dynamics",
    "ntu_truncate": "dynamics",
    "svd_precut_bond": "dynamics",
    "nonselective_round": "dynamics",
    "gap_rank": "dynamics",
    # sampler [A3]
    "pepo_trace": "sampler",
    "NormCache": "sampler",
    "norm_cache": "sampler",
    "expect_site_caps": "sampler",
    "stab_expectation": "sampler",
    "born_sample_round": "sampler",
    "terminal_readout_obs": "sampler",
    "terminal_readout_obs_prob": "sampler",
    "s_to_det": "sampler",
    "det_to_s": "sampler",
    "negativity_witness": "sampler",
    "C3Stats": "sampler",
}

__all__ = sorted(_EXPORTS)


def __getattr__(name: str):
    mod = _EXPORTS.get(name)
    if mod is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return getattr(import_module(f".{mod}", __name__), name)


def __dir__() -> list:
    return sorted(set(globals()) | set(_EXPORTS))

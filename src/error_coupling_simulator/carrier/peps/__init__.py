r"""Single-wire (pure-state) 2D qutrit PEPS trajectory carrier — the RUNG-B
feasibility spike (``docs/nonpauli_teacher/peps_singlewire_spike_contract.md``
v1.0 REGISTERED).

The public surface of the spike engine, grouped by submodule:

  * :mod:`.state` — :class:`PepsState`, :func:`build_codestate_peps` (single-wire
    codestate, pepo steps 1-3 + norm-normalize), :func:`dense_psi` (d3 referee
    bridge), the 1-site apply + local gate table (referee-independent, D4);
  * :mod:`.stab_tt` — the UNSQUARED ``sqrt(E_s)`` diagonal TT (SF3 rank bound
    ``(3,5,3)``/``(3,)``) + :func:`apply_stab_branch`;
  * :mod:`.contraction` — the double-layer ``<psi| Pi |psi>`` boundary-MPS reads
    (SF9), the two-term Born read, the §6.2 per-read accuracy instruments, the
    terminal POVM + exact-P(obs) seam;
  * :mod:`.trajectory` — the per-shot loop (D7 — the ``mps_forward`` value
    contracts transplanted to 2D), the §6.1 dynamic-eps truncation policy, the
    :class:`PepsSampler` packed-record driver;
  * :mod:`.sampling_maps` — the three pinned uniform->outcome decision maps
    (single source; SW5/SW6-testable);
  * :mod:`.diagnostics` — :func:`bond_profile` (the SW8 instrument), :func:`eps_l`
    (the §6.3 Rudolph-Tindall loop-correlation instrument), :func:`loop_rank_probe`.

``s_to_det`` / ``det_to_s`` are re-exported from the carrier-neutral
``carrier.record_fold`` module (contract §3 / SF11 — single source; the XOR
detector fold is applied by the package-local packed-record boundary before a
consumer receives a ``det`` payload).
"""

from ..record_fold import det_to_s, s_to_det
from .contraction import (
    NormCache,
    born_read_stab,
    branch_norm_sq,
    chib_doubling_delta,
    cross_route_q1,
    expect_double_layer,
    expect_site_caps,
    norm_cache,
    norm_read,
    site_rdm,
    stab_site_ops,
    terminal_collapse_diag,
    terminal_effect_pair,
    terminal_obs_prob,
)
from .diagnostics import bond_profile, eps_l, loop_rank_probe, max_bond
from .sampling_maps import (
    leak_branch_from_uniform,
    sbit_from_uniform,
    terminal_bit_from_uniform,
)
from .stab_tt import (
    SingleWireStabTT,
    apply_stab_branch,
    leaked_weight,
    stab_tt_singlewire,
    tt_rank_bounds,
)
from .state import (
    CDTYPE,
    QUTRIT,
    RDTYPE,
    PepoLayout,
    PepsState,
    apply_gate_1site,
    apply_site_op,
    build_codestate_peps,
    dense_psi,
    fused_bond_name,
    phys_name,
    qutrit_gate,
    renormalize,
    site_tag,
    site_tensor,
)
from .trajectory import (
    D_ABORT_DEFAULT,
    W_MAX_DEFAULT,
    BondAbortError,
    PepsSampler,
    TruncationPolicy,
    dynamic_truncate,
    leak_sample,
    run_trajectory,
    sample_stab,
    terminal_readout,
    truncate_bond_dcap,
    truncate_bond_lossless,
    truncate_bond_policy,
    truncate_path_bonds,
)

__all__ = [
    # state
    "CDTYPE", "RDTYPE", "QUTRIT", "PepoLayout", "PepsState",
    "apply_gate_1site", "apply_site_op", "build_codestate_peps", "dense_psi",
    "fused_bond_name", "phys_name", "qutrit_gate", "renormalize", "site_tag",
    "site_tensor",
    # stab_tt
    "SingleWireStabTT", "apply_stab_branch", "leaked_weight",
    "stab_tt_singlewire", "tt_rank_bounds",
    # contraction
    "NormCache", "norm_cache", "expect_double_layer", "expect_site_caps",
    "norm_read", "site_rdm", "born_read_stab", "branch_norm_sq",
    "cross_route_q1", "chib_doubling_delta", "stab_site_ops",
    "terminal_obs_prob", "terminal_effect_pair", "terminal_collapse_diag",
    # trajectory
    "TruncationPolicy", "truncate_bond_policy", "truncate_bond_dcap",
    "truncate_bond_lossless", "dynamic_truncate", "truncate_path_bonds",
    "leak_sample", "sample_stab", "terminal_readout", "run_trajectory",
    "PepsSampler", "BondAbortError", "W_MAX_DEFAULT", "D_ABORT_DEFAULT",
    # sampling maps
    "sbit_from_uniform", "terminal_bit_from_uniform", "leak_branch_from_uniform",
    # diagnostics
    "bond_profile", "max_bond", "eps_l", "loop_rank_probe",
    # record fold (verbatim re-export, single source)
    "s_to_det", "det_to_s",
]

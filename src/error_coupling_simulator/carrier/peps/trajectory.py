from __future__ import annotations

r"""Per-shot single-wire PEPS trajectory loop.

Sampling maps are owned by ``sampling_maps.py``:

  * stabilizer: ``sbit = 0 iff u < p0`` (STRICT ``<``), ``p0 = 1/2 (1 + <P>)``
    read through the double-layer caps path;
  * LEAK Kraus selection: branch ``k`` = the FIRST ``k`` with
    ``u * tot <= cumsum_k`` (non-strict ``<=``), fallback ``K - 1``;
    ``p_k`` comes from the double-layer 1-site RDM;
  * terminal: ALL ``n_data`` qutrits in ENGINE order, one uniform each,
    ``bit = 1 iff u < p1``, ``sqrt(F_bit)`` collapse per site, ALL X-logical
    sites H-rotated UP-FRONT, obs = parity(logical-support bits) XOR ``m``
    under the declared terminal instrument.

RNG: per-shot ``np.random.default_rng((base_seed, shot))``; gates draw nothing;
one uniform is used per leakage site operation, one per
stabilizer; ``n_data`` at the terminal. Instrument reads consume no host
uniforms (their fit seeds are separate torch generators).

Only arm A is supported; arm C (leak-flag draws) raises.

Dynamic-epsilon policy: the reused cutters ``svd_precut_bond`` and
``ntu_truncate`` have no dynamic mode. Call order per truncation event is: apply
the TT branch, then over the
path bonds pass 1 (``svd_precut_bond``) — ALL bonds — then pass 2
(``ntu_truncate``) — ALL bonds (all precuts land before any NTU metric build, so
no metric leg exceeds ``W_max``). BOTH passes compute the full SVD of their
CURRENT pair insertion before cutting; the running target ``r_dyn`` = the
smallest rank whose squared-sigma tail (RELATIVE, local insertion spectrum) is
``<= eps_spike``. Precut window = ``min(4 * r_dyn, W_max)``, ``W_max = 160 =
4 * D_abort``. The total per-cut discarded mass (precut plus policy cut,
both squared-sigma relative tails, summed) ``<= eps_spike``; a W_max-capped
precut that WOULD exceed it ledgers a ``window_binding`` flag entry and retries
ONCE with the kept rank escalated (the uncapped ``4 * r_dyn`` window); still
exceeding => the PRECONDITION tripwire (orderly stop), never data. The widening
machinery is defensive and normally unreachable below ``W_max``. Pass 2's kept
rank consumes the remaining epsilon budget
(``eps_spike - precut_discarded``) — the invariant-enforcing form of the
running-target rule (identical to the plain rule whenever the precut tail is
negligible, i.e. everywhere below the window boundary).

GPU-only, complex128, with a local gate table independent of the exact reference.
"""

from dataclasses import dataclass

import numpy as np
import torch

from ...numerics import NUMERICAL_ZERO
from ..within_cycle import (
    CPTP_TOL,
    SV_GATE_IDS,
    SV_GATE_NAMES,
    WC_OP_GATE,
    WC_OP_LEAK,
    WithinCycleScheduleHost,
)
from ..pepo.dynamics import _bond_between, _qr_split, ntu_truncate, svd_precut_bond
from ..records import PackedShotBatch, pack_raw_syndrome_shots
from .contraction import (
    born_read_stab,
    chib_doubling_delta,
    cross_route_q1,
    expect_double_layer,
    norm_cache,
    norm_read,
    terminal_collapse_diag,
    terminal_effect_pair,
)
from .diagnostics import bond_profile
from .sampling_maps import (
    leak_branch_from_uniform,
    sbit_from_uniform,
    terminal_bit_from_uniform,
)
from .state import (
    CDTYPE,
    PepsState,
    apply_site_op,
    build_codestate_peps,
    qutrit_gate,
    renormalize,
)
from .stab_tt import stab_tt_singlewire, apply_stab_branch

#: Metric-feasibility precut cap: W_max = 4 * D_abort. Pass 1
#: bounds every path bond to <= W_max BEFORE any pass-2 NTU metric is built.
W_MAX_DEFAULT = 160
#: Grown-dimension abort: fires when any grown dimension exceeds 40.
#: D = 40 itself is processed; the check occurs before metric construction.
D_ABORT_DEFAULT = 40

class BondAbortError(RuntimeError):
    """Orderly stop when a grown path-bond dimension exceeds ``D_abort``.

    Carries the offending bond and full bond profile for diagnostic recovery.
    """

    def __init__(self, message: str, bond: str, dim: int, profile: dict) -> None:
        super().__init__(message)
        self.bond = str(bond)
        self.dim = int(dim)
        self.profile = dict(profile)


# --------------------------------------------------------------------------- #
# Truncation policy                                                            #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class TruncationPolicy:
    """The declared per-run truncation mode: dynamic epsilon, fixed cap,
    lossless gauge compression, or environment-aware ``fet_env``.

    ``mode``: ``"dynamic_eps"`` (requires ``eps_spike``), ``"d_cap"``
    (the parent two-pass at a fixed integer target — requires ``D_cap``),
    ``"lossless"`` (no cut below the exact local rank — the
    ``sigma > 1e-12 sigma_1`` count; a zero-drop gauge compression only), or
    ``"fet_env"`` (the environment-aware truncator — requires ``eps_fid``;
    a strict pass-1 no-op followed by per-bond-sequential truncation in pass 2,
    via :mod:`.fet`). ``W_max``
    is the precut cap for the dynamic arm only.
    """

    mode: str
    eps_spike: float | None = None
    D_cap: int | None = None
    W_max: int = W_MAX_DEFAULT
    eps_fid: float | None = None

    def __post_init__(self) -> None:
        if self.mode not in ("dynamic_eps", "d_cap", "lossless", "fet_env"):
            raise ValueError(f"unknown truncation mode {self.mode!r}")
        if self.mode == "dynamic_eps":
            if self.eps_spike is None or not float(self.eps_spike) > 0.0:
                raise ValueError(f"dynamic_eps requires eps_spike > 0 (got {self.eps_spike})")
            if int(self.W_max) < 1:
                raise ValueError(f"W_max must be >= 1 (got {self.W_max})")
        if self.mode == "d_cap" and (self.D_cap is None or int(self.D_cap) < 1):
            raise ValueError(f"d_cap requires D_cap >= 1 (got {self.D_cap})")
        if self.mode == "fet_env" and (self.eps_fid is None or not float(self.eps_fid) > 0.0):
            # fet_env does not require eps_spike: its pass 1 is a
            # strict NO-OP, so it never reads the dynamic-eps window budget.
            raise ValueError(f"fet_env requires eps_fid > 0 (got {self.eps_fid})")


def _insertion_spectrum(state: PepsState, bond: str) -> torch.Tensor:
    """The descending singular-value spectrum of the CURRENT pair insertion
    ``X0 = R_A R_B^T`` of ``bond`` (the pre-cut spectrum probe; the same
    QR-split object the reused cutters recompute internally)."""
    tids = tuple(state.tn.ind_map[bond])
    assert len(tids) == 2, f"bond {bond!r} must join exactly 2 tensors (got {len(tids)})"
    ta, tb = (state.tn.tensor_map[tid] for tid in tids)
    _QA, RA, _ia, _da = _qr_split(ta, bond)
    _QB, RB, _ib, _db = _qr_split(tb, bond)
    return torch.linalg.svdvals(RA @ RB.mT)


def _sq_tail(S: torch.Tensor, r: int) -> float:
    """Relative squared-sigma tail beyond kept rank ``r``:
    normalized by the local insertion spectrum's sum of sigma^2)."""
    s_sq = (S * S).real
    tot = float(s_sq.sum())
    if tot <= 0.0:
        return 0.0
    r = max(0, int(r))
    return float(s_sq[r:].sum()) / tot


def _rank_for_tail(S: torch.Tensor, eps: float) -> int:
    """The running target ``r_dyn``: the smallest kept rank whose relative
    squared-sigma tail is ``<= eps`` on the given spectrum (always exists — the
    full-rank tail is 0)."""
    n = int(S.numel())
    if n == 0:
        return 1
    s_sq = (S * S).real
    tot = float(s_sq.sum())
    if tot <= 0.0:
        return 1
    # suffix sums: tail(r) = sum_{k >= r} / tot for kept rank r
    tail = torch.flip(torch.cumsum(torch.flip(s_sq, dims=(0,)), dim=0), dims=(0,))
    for r in range(1, n + 1):
        t = float(tail[r]) / tot if r < n else 0.0
        if t <= float(eps):
            return r
    return n


def _exact_rank(S: torch.Tensor) -> int:
    """The exact local rank under the ``sigma > 1e-12 sigma_1`` zero-drop
    convention."""
    if S.numel() == 0 or float(S[0]) <= 0.0:
        return 1
    return max(1, int((S > NUMERICAL_ZERO * float(S[0])).sum()))


def _policy_precut(state: PepsState, bond: str, policy: TruncationPolicy) -> dict:
    """Pass 1 of :func:`truncate_bond_policy` on one bond (see the module
    docstring for the window and invariant machinery). Returns the per-bond
    pass-1 record consumed by pass 2; ``precut_discarded`` is 0.0 EXACTLY when
    no precut ran."""
    dim_in = int(state.tn.ind_size(bond))
    # the pre-cut insertion spectrum is computed ONCE for all modes: it gives
    # the exact local rank reported in the ledger and, for the
    # dynamic arm, the running target r_dyn.
    S = _insertion_spectrum(state, bond)
    exact_rank = _exact_rank(S)
    rec = {"bond": str(bond), "dim_in": dim_in, "precut_discarded": 0.0,
           "window_binding": False, "r_dyn": None, "width": None,
           "exact_rank": int(exact_rank)}
    if policy.mode == "lossless":
        rec["r_dyn"] = int(exact_rank)
        if dim_in > exact_rank:
            entry = svd_precut_bond(state, bond, exact_rank)  # zero-drop gauge compression
            rec["precut_discarded"] = float(entry["discarded"])
        return rec
    if policy.mode == "d_cap":
        cap4 = 4 * int(policy.D_cap)
        rec["width"] = cap4
        if dim_in > cap4:
            entry = svd_precut_bond(state, bond, cap4)
            rec["precut_discarded"] = float(entry["discarded"])
        return rec
    if policy.mode == "fet_env":
        # Pass 1 is a strict no-op for
        # fet_env — leave the bond at FULL dim so pass-2's `gamma_TN` reads the
        # UN-pre-truncated environment. `rec` already carries EXACTLY the keys
        # `_policy_cut`'s summary reads (precut_discarded=0.0, r_dyn=None,
        # width=None, window_binding=False, exact_rank); no `svd_precut_bond`
        # runs. Placed BEFORE the dynamic_eps tail so fet_env never reaches
        # `float(policy.eps_spike)` (= `float(None)` -> TypeError).
        return rec

    # dynamic-epsilon policy
    eps = float(policy.eps_spike)
    r_dyn = _rank_for_tail(S, eps)
    width = min(4 * r_dyn, int(policy.W_max))
    rec["r_dyn"] = int(r_dyn)
    rec["width"] = int(width)
    if dim_in > width:
        # predictive invariant check on the CURRENT spectrum: precut tail at the
        # capped window + the pass-2 tail on the kept spectrum (the post-precut
        # insertion spectrum IS S[:width] — the precut write-back is that SVD cut).
        pre_tail = _sq_tail(S, width)
        r2 = _rank_for_tail(S[:width], max(eps - pre_tail, 0.0))
        total_pred = pre_tail + (1.0 - pre_tail) * _sq_tail(S[:width], r2)
        if total_pred > eps:
            # The W_max-capped precut would exceed the invariant: flag and
            # ONE retry with the kept rank escalated (the uncapped window).
            state.ledger.append({
                "op": "window_binding",
                "bond": str(bond),
                "dim_in": dim_in,
                "r_dyn": int(r_dyn),
                "width_capped": int(width),
                "W_max": int(policy.W_max),
                "pre_tail": float(pre_tail),
                "total_pred": float(total_pred),
                "eps_spike": eps,
            })
            rec["window_binding"] = True
            width = 4 * r_dyn
            rec["width"] = int(width)
            if dim_in > width:
                pre_tail = _sq_tail(S, width)
                r2 = _rank_for_tail(S[:width], max(eps - pre_tail, 0.0))
                total_pred = pre_tail + (1.0 - pre_tail) * _sq_tail(S[:width], r2)
                if total_pred > eps:
                    raise RuntimeError(
                        f"precondition: total-discard "
                        f"invariant unsatisfiable at bond {bond!r} after the ONE "
                        f"retry (total_pred={total_pred:.3e} > "
                        f"eps_spike={eps:.3e})")
        if dim_in > width:
            entry = svd_precut_bond(state, bond, int(width))
            rec["precut_discarded"] = float(entry["discarded"])
    return rec


def _policy_cut(state: PepsState, bond: str, policy: TruncationPolicy,
                rec: dict) -> dict:
    """Pass 2 of :func:`truncate_bond_policy` on one bond + the per-bond summary
    ledger entry (``op='policy_truncate'``; ``total_discarded`` = precut +
    policy-cut squared-sigma relative tails).

    For the ``fet_env`` mode this does the
    WHOLE truncation, PER-BOND SEQUENTIAL on the CURRENT (post-prior-write)
    state, and ledgers ``op='fet_truncate'`` — see the early-return branch."""
    if policy.mode == "fet_env":
        # Build Γ on the state left by the prior bond's write-back. The
        # sweep order is fixed + load-bearing — each Γ reflects already-truncated
        # neighbours). `fet` is imported LAZILY here to avoid the fet<->trajectory
        # import cycle (fet imports `_exact_rank`/`_insertion_spectrum` from this
        # module at load time). fet_env is a slow diagnostic mode:
        # `gamma_TN` recomputes a full double-layer contraction per bond — it runs
        # ONCE inside `env_optimal_rank`, which returns the achieved env-fidelity
        # so we do not rebuild `Gamma` here just to re-score the ledger (no
        # double `gamma_TN` per bond).
        from .fet import apply_fet_truncation, env_optimal_rank
        dim_in = int(state.tn.ind_size(bond))
        env_rank, U, Vh, fid_g = env_optimal_rank(state, bond, float(policy.eps_fid))
        apply_fet_truncation(state, bond, U, Vh)
        summary = {
            "op": "fet_truncate",
            "mode": policy.mode,
            "bond": str(bond),
            "dim_in": int(dim_in),
            "dim_out": int(state.tn.ind_size(bond)),
            "exact_rank": rec.get("exact_rank"),
            "env_rank": int(env_rank),
            "Fid_gamma": float(fid_g),  # ASCII ledger key for Fid_Γ
            "eps_fid": float(policy.eps_fid),
        }
        state.ledger.append(summary)
        return summary
    ntu_disc = 0.0
    kept_target = None
    if policy.mode == "d_cap":
        kept_target = int(policy.D_cap)
        if int(state.tn.ind_size(bond)) > kept_target:
            entry = ntu_truncate(state, bond, kept_target)
            ntu_disc = float(entry["discarded"])
    elif policy.mode == "dynamic_eps":
        eps = float(policy.eps_spike)
        S2 = _insertion_spectrum(state, bond)  # pass 2 recomputes before cutting
        eps_rem = max(eps - float(rec["precut_discarded"]), 0.0)
        kept_target = _rank_for_tail(S2, eps_rem)
        if int(state.tn.ind_size(bond)) > kept_target:
            entry = ntu_truncate(state, bond, kept_target)
            ntu_disc = float(entry["discarded"])
    # lossless: no pass-2 cut by definition.
    total = float(rec["precut_discarded"]) + ntu_disc
    summary = {
        "op": "policy_truncate",
        "mode": policy.mode,
        "bond": str(bond),
        "dim_in": int(rec["dim_in"]),
        "dim_out": int(state.tn.ind_size(bond)),
        "exact_rank": rec.get("exact_rank"),
        "r_dyn": rec["r_dyn"],
        "width": rec["width"],
        "kept_target": kept_target,
        "precut_discarded": float(rec["precut_discarded"]),
        "ntu_discarded": float(ntu_disc),
        "total_discarded": total,
        "window_binding": bool(rec["window_binding"]),
        "eps_spike": (float(policy.eps_spike) if policy.mode == "dynamic_eps" else None),
        "D_cap": (int(policy.D_cap) if policy.mode == "d_cap" else None),
    }
    state.ledger.append(summary)
    return summary


def truncate_bond_policy(state: PepsState, bond: str, policy: TruncationPolicy) -> dict:
    """Both truncation passes on one bond under the declared policy arm.
    For a grown path use :func:`truncate_path_bonds`; the
    all-precuts-before-any-metric ordering is what bounds every NTU metric leg
    to ``W_max``. ``policy`` must be a :class:`TruncationPolicy` (a
    ``TypeError`` on anything else — so a caller passing a bare int/eps falls
    through cleanly to the dedicated helpers below)."""
    if not isinstance(policy, TruncationPolicy):
        raise TypeError(
            "truncate_bond_policy needs a TruncationPolicy; use truncate_bond_dcap / "
            "truncate_bond_lossless / dynamic_truncate for the bare-argument forms")
    rec = _policy_precut(state, bond, policy)
    return _policy_cut(state, bond, policy, rec)


def truncate_bond_dcap(state: PepsState, bond: str, d_cap: int) -> dict:
    """The D_cap truncation arm on one bond (convenience wrapper — the parent
    two-pass at a fixed integer target)."""
    return truncate_bond_policy(state, bond, TruncationPolicy("d_cap", D_cap=int(d_cap)))


def truncate_bond_lossless(state: PepsState, bond: str) -> dict:
    """The structural lossless arm on one bond (convenience wrapper; no cut
    below the exact local rank, the ``sigma > 1e-12 sigma_1`` count)."""
    return truncate_bond_policy(state, bond, TruncationPolicy("lossless"))


def dynamic_truncate(state: PepsState, bond: str, *, eps_spike: float,
                     w_max: int = W_MAX_DEFAULT) -> dict:
    """The dynamic-epsilon arm on one bond, exposing the ``w_max`` window cap.
    Propagates an orderly-stop ``RuntimeError`` if the discard invariant cannot
    be satisfied."""
    return truncate_bond_policy(
        state, bond,
        TruncationPolicy("dynamic_eps", eps_spike=float(eps_spike), W_max=int(w_max)))


def truncate_path_bonds(state: PepsState, bonds: list, policy: TruncationPolicy) -> list:
    """Two-pass truncation over a grown support path: pass 1
    (``svd_precut_bond`` under the policy window) over ALL bonds, THEN pass 2
    (``ntu_truncate`` at the running target) over ALL bonds — so no pass-2
    metric cluster ever doubles an un-precut fat neighbor bond."""
    recs = [(_policy_precut(state, bond, policy), bond) for bond in bonds]
    return [_policy_cut(state, bond, policy, rec) for rec, bond in recs]


# --------------------------------------------------------------------------- #
# Trajectory operations                                                       #
# --------------------------------------------------------------------------- #
def leak_sample(state: PepsState, kraus: list, pos: int, u: float, *,
                cache=None, R_n: int | None = None, fit_seed: int = 0) -> int:
    """MCWF Kraus-sample one leakage site operation: branch
    ``k`` w.p. ``p_k = <psi| K_k^dag K_k |psi>`` read from the double-layer
    one-site RDM (one contraction plus 3x3 traces), selection by the
    declared tie break: the first ``k`` with
    ``u * tot <= cumsum_k`` (NON-STRICT ``<=``), fallback ``K - 1``. ONE uniform
    ``u`` consumed. Kraus completeness is asserted to 1e-12. A one-site
    Kraus is bond-inert; ``psi <- K_k psi / sqrt(p_k)``.
    """
    from .contraction import site_rdm  # local: keep the import graph flat

    dev = torch.device(state.device)
    ks = [torch.as_tensor(K, dtype=CDTYPE, device=dev) for K in kraus]
    comp = torch.zeros((3, 3), dtype=CDTYPE, device=dev)
    for K in ks:
        comp = comp + K.conj().mT @ K
    resid = float((comp - torch.eye(3, dtype=CDTYPE, device=dev)).abs().max())
    assert resid <= CPTP_TOL, (
        f"Kraus completeness violated (max|sum K^dag K - I| = {resid:.3e})")

    # Norm-cache threading: the RDM read is the SINGLE read on this
    # (unmutated) snapshot; own its cache here so ``apply_site_op`` below leaves
    # it stale (a stale NormCache is the caller's bug — the local var is dropped
    # on return). Boundary route only: R_n is None is the d3 exact route — cache
    # stays None and ``site_rdm`` takes the exact full-double-layer path
    # (INVARIANT: byte-identical d3). Building the cache here vs. letting
    # ``site_rdm`` build it internally is the SAME single reverse sweep.
    if cache is None and R_n is not None:
        cache = norm_cache(state, R_n, fit_seed)
    rdm = site_rdm(state, int(pos), cache=cache, R_n=R_n, fit_seed=fit_seed)
    pk = [float(torch.einsum("ab,ba->", K.conj().mT @ K, rdm).real) for K in ks]
    tot = float(sum(pk))
    if not tot > NUMERICAL_ZERO:
        raise RuntimeError(f"leak_sample: nonpositive total branch mass {tot:.6e} at pos {pos}")
    sel = leak_branch_from_uniform(u, pk)  # tie-break rule is owned by sampling_maps
    apply_site_op(state, int(pos), ks[sel])
    renormalize(state, pk[sel])
    return int(sel)


def sample_stab(state: PepsState, paulis: dict, u: float, b: float, arm: str,
                policy: TruncationPolicy, *,
                R_n: int | None = None, R_x: int | None = None, fit_seed: int = 0,
                d_abort: int | None = None, cross_route: bool = False,
                chib_chi_b: int | None = None) -> int:
    """One stabilizer Born measurement plus selective update:

      1. ``(N, M, p0)`` through the PRODUCTION caps path (two-term identity);
      2. optional cross-route and chi_b-doubling instrument reads, ledgered
         — NO host uniforms consumed;
      3. ``sbit = 0 iff u < p0`` using strict ``<``;
      4. selective ``sqrt(E_s)`` TT branch (measured ranks ledgered);
      5. the D_abort pre-metric check on the GROWN dims (fires on dim
         ``> d_abort``; ``D_abort`` itself is processed), raising
         :class:`BondAbortError` (orderly stop);
      6. two-pass truncation under the discard invariant;
      7. renormalize to unit norm + the renorm ledger entry.
    """
    paulis = {int(k): str(v).upper() for k, v in paulis.items()}
    # Norm-cache threading: ONE reverse-pass NormCache per PRE-branch
    # snapshot, shared by the N and M legs of the single ``born_read_stab`` AND
    # the cross-route and chi_b instruments; all read the same unmutated
    # state. The norm right-environments are op-agnostic (identity columns beyond
    # the op support), so a norm cache at R_n serves BOTH the N read and the M
    # read whenever R_x == R_n; otherwise the
    # M leg gets its own cache at R_x. INVARIANT: R_n is None is the d3 exact
    # route — cache_n/cache_x stay None, every read takes the exact
    # full-double-layer path, so the d3 gates are byte-identical.
    cache_n = norm_cache(state, R_n, fit_seed) if R_n is not None else None
    if R_x is None:
        cache_x = None
    elif R_n is not None and int(R_x) == int(R_n):
        cache_x = cache_n
    else:
        cache_x = norm_cache(state, R_x, fit_seed)
    N, M, p0 = born_read_stab(state, paulis, b, arm, cache_n=cache_n, cache_x=cache_x,
                              R_n=R_n, R_x=R_x, fit_seed=fit_seed)
    if cross_route:
        state.ledger.append(cross_route_q1(state, paulis, b, arm,
                                           cache_n=cache_n, cache_x=cache_x,
                                           R_n=R_n, R_x=R_x, fit_seed=fit_seed))
    if chib_chi_b is not None:
        state.ledger.append(chib_doubling_delta(state, paulis, b, arm,
                                                int(chib_chi_b), cache=cache_n,
                                                fit_seed=fit_seed))

    sbit = sbit_from_uniform(u, p0)  # strict <; single source: sampling_maps

    tt = stab_tt_singlewire(paulis, sbit, b, arm, state.layout, state.device)
    state.ledger.append({
        "op": "stab_tt_ranks",
        "path": tuple(int(p) for p in tt.path),
        "outcome": int(sbit),
        "ranks": tuple(int(r) for r in tt.ranks),
    })
    apply_stab_branch(state, tt)

    path_bonds = [bn for bn in (_bond_between(state, a, bpos)
                                for a, bpos in zip(tt.path, tt.path[1:]))
                  if bn is not None]
    if d_abort is not None:
        for bond in path_bonds:
            dim = int(state.tn.ind_size(bond))
            if dim > int(d_abort):  # D_abort itself is processed
                err = BondAbortError(
                    f"D_abort={int(d_abort)}: grown bond {bond!r} dim {dim} exceeds "
                    f"the pre-metric abort threshold",
                    bond=bond, dim=dim, profile=bond_profile(state))
                raise err

    truncate_path_bonds(state, path_bonds, policy)

    norm2 = norm_read(state, R_n=R_n, fit_seed=fit_seed)
    renormalize(state, norm2)
    state.ledger.append({
        "kind": "renorm",
        "outcome": int(sbit),
        "p0": float(p0),
        "N": float(N),
        "M": float(M),
        "norm_raw": float(norm2),
        "tt_ranks": tuple(int(r) for r in tt.ranks),
    })
    return int(sbit)


def terminal_readout(state: PepsState, log_sites: list, log_isx: list, n_data: int,
                     b_eff: float, m: int, u_draws: list, *,
                     R_n: int | None = None, fit_seed: int = 0) -> tuple[int, list]:
    """The terminal transversal data readout, matching
    ``mps_forward._terminal_readout`` values:

      * ALL X-logical sites H-rotated UP-FRONT before the first read
        (value-identical to per-site conjugation: disjoint sites);
      * ALL ``n_data`` qutrits in ENGINE order, one uniform each:
        ``p1 = <F1> / <psi|psi>`` (``F1 = |1><1| + b|2><2|``), ``bit = 1 iff
        u < p1``, ``sqrt(F_bit)`` collapse + renormalize per site;
      * obs = **parity over the LOGICAL SUPPORT only** XOR ``m``.

    The state is CONSUMED (mutated; no post-terminal use). Returns
    ``(obs, bits)`` with ``bits`` the per-qutrit engine-order record.
    """
    dev = torch.device(state.device)
    h = qutrit_gate("H", dev)
    x_log = [int(log_sites[j]) for j in range(len(log_sites)) if int(log_isx[j]) == 1]
    for s in x_log:
        apply_site_op(state, s, h)

    _f0, f1 = terminal_effect_pair(b_eff, dev)
    bits: list[int] = []
    for q in range(int(n_data)):
        # Norm-cache threading: ``den`` (the norm) and ``num1`` (the site-q
        # F1 caps read) are BOTH on the current PRE-collapse snapshot — one
        # reverse-pass cache serves both. The ``apply_site_op`` collapse below
        # mutates the state, so the cache is dropped (a stale NormCache is the
        # caller's bug) and the post-collapse ``norm_read`` rebuilds. INVARIANT:
        # R_n is None is the d3 exact route — cache stays None, both reads take
        # the exact full-double-layer path (byte-identical d3).
        cache = norm_cache(state, R_n, fit_seed) if R_n is not None else None
        den = norm_read(state, cache=cache, R_n=R_n, fit_seed=fit_seed)
        if not den > NUMERICAL_ZERO:
            raise RuntimeError(
                f"terminal_readout: nonpositive trace {den:.6e} at qutrit {q}")
        num1 = expect_double_layer(state, {q: f1}, cache=cache, R_n=R_n,
                                   fit_seed=fit_seed).real
        p1 = min(1.0, max(0.0, num1 / den))
        bit = terminal_bit_from_uniform(u_draws[q], p1)  # bit=1 iff u<p1 (single source)
        apply_site_op(state, q, terminal_collapse_diag(bit, b_eff, dev))
        renormalize(state, norm_read(state, R_n=R_n, fit_seed=fit_seed))
        bits.append(int(bit))

    parity = 0
    for q in log_sites:
        parity ^= bits[int(q)] & 1
    return int((parity ^ (int(m) & 1)) & 1), bits


def run_trajectory(codestate: PepsState, marsh, leak_kraus: list, gate_table: dict,
                   stab_supp: np.ndarray, stab_isx: np.ndarray, stab_len: np.ndarray,
                   log_sites: list, log_isx: list, arm: str, b: float, b_eff: float,
                   m: int, policy: TruncationPolicy, n_data: int, R: int,
                   rng: np.random.Generator, *,
                   R_n: int | None = None, R_x: int | None = None, fit_seed: int = 0,
                   d_abort: int | None = None,
                   cross_route_pred=None, chib_pred=None, chi_b: int | None = None,
                   round_hook=None) -> tuple:
    """Evolve one single-wire PEPS trajectory using ``mps_forward``
    value semantics on the two-dimensional grid; engine positions are the
    grid positions, no snake map). Returns ``(syndrome_bits round-major, obs,
    terminal bits, final PepsState)`` — the final state carries the ledger.

    Draw order: per round, the
    PRE-measure CSR segment (GATE: no draw; LEAK: one uniform), the ``n_stab``
    stabilizers in schedule order (one uniform each), the POST-measure segment
    (the transversal Y; a LEAK op there would draw — mirrored), then ``n_data``
    terminal uniforms in engine order. ``round_hook(state, r)`` runs after each
    round's last operation; ``cross_route_pred(r, j)`` and ``chib_pred(r, j)``
    gate the optional diagnostic reads.
    """
    if str(arm).upper() == "C":
        raise ValueError("arm C is unsupported by this trajectory; arm A is required")
    state = codestate.copy()
    round_op_ptr = marsh.round_op_ptr.detach().cpu().numpy()
    op_kind = marsh.op_kind.detach().cpu().numpy()
    op_uid = marsh.op_uid.detach().cpu().numpy()
    op_site = marsh.op_site.detach().cpu().numpy()
    syndrome_bits: list[int] = []

    for r in range(int(R)):
        # PRE-measure op segment (GATE / LEAK), CSR order — draws consumed as walked.
        pre0, pre1 = int(round_op_ptr[2 * r]), int(round_op_ptr[2 * r + 1])
        for t in range(pre0, pre1):
            site = int(op_site[t])
            if int(op_kind[t]) == WC_OP_GATE:
                apply_site_op(state, site, gate_table[int(op_uid[t])])
            elif int(op_kind[t]) == WC_OP_LEAK:
                u = float(rng.random())
                leak_sample(state, leak_kraus, site, u, R_n=R_n, fit_seed=fit_seed)
            else:
                raise AssertionError(f"unknown op_kind {int(op_kind[t])} at op {t}")
        # measure all stabilizers (schedule order).
        for s_idx in range(int(marsh.n_stab)):
            slen = int(stab_len[s_idx])
            paulis = {int(stab_supp[s_idx, k]): ("X" if int(stab_isx[s_idx, k]) else "Z")
                      for k in range(slen)}
            u_out = float(rng.random())
            cr = bool(cross_route_pred(r, s_idx)) if cross_route_pred is not None else False
            cb = int(chi_b) if (chib_pred is not None and chib_pred(r, s_idx)) else None
            bit = sample_stab(state, paulis, u_out, b, arm, policy,
                              R_n=R_n, R_x=R_x, fit_seed=fit_seed, d_abort=d_abort,
                              cross_route=cr, chib_chi_b=cb)
            syndrome_bits.append(int(bit))
        # POST-measure op segment (the transversal Y; empty terminal round).
        post0, post1 = int(round_op_ptr[2 * r + 1]), int(round_op_ptr[2 * r + 2])
        for t in range(post0, post1):
            site = int(op_site[t])
            if int(op_kind[t]) == WC_OP_GATE:
                apply_site_op(state, site, gate_table[int(op_uid[t])])
            elif int(op_kind[t]) == WC_OP_LEAK:
                u = float(rng.random())
                leak_sample(state, leak_kraus, site, u, R_n=R_n, fit_seed=fit_seed)
        if round_hook is not None:
            round_hook(state, r)

    u_term = [float(rng.random()) for _ in range(int(n_data))]
    obs, bits = terminal_readout(state, log_sites, log_isx, int(n_data), b_eff, m,
                                 u_term, R_n=R_n, fit_seed=fit_seed)
    return syndrome_bits, obs, bits, state


# --------------------------------------------------------------------------- #
# Packed-record sampler                                                       #
# --------------------------------------------------------------------------- #
class PepsSampler:
    """Single-wire 2D PEPS trajectory sampler — consume an explicit schedule,
    marshal it through the package-local host, then build the
    codestate PEPS -> N trajectories -> package-local :class:`PackedShotBatch`.

    The packed byte payload retains raw per-round ``s`` bits in round-major
    order, but the public ``to_det_obs()`` / ``to_record_batch()`` boundary
    applies the simulator's temporal XOR fold.  Raw syndrome access is explicit
    through ``to_raw_syndrome_obs()``.  Every artifact carries the
    compiled/data-register label.
    """

    def __init__(
        self,
        device: str | torch.device = "cuda",
        *,
        host=None,
    ) -> None:
        self.device = torch.device(device)
        self._host = (
            WithinCycleScheduleHost(self.device) if host is None else host)

    @property
    def host(self):
        """The injected schedule/marshalling host (read-only)."""

        return self._host

    def sample(self, spec, *, sched=None, policy: TruncationPolicy,
               R_n: int | None = None, R_x: int | None = None, fit_seed: int = 0,
               materialize: bool = True, d_abort: int | None = None,
               cross_route_pred=None, chib_pred=None, chi_b: int | None = None,
               round_hook=None) -> tuple:
        """Run a PEPS trajectory job; returns ``(PackedShotBatch, per-shot ledgers)``.

        Mirrors ``MpsLeakageForward.sample``'s host reuse: ``spec`` is an
        ``sv_sampler.RunSpec``; ``sched`` must carry the within-cycle interior
        streams (the r01-geometry + r10-interior split). ``round_hook`` (if any)
        is called as ``round_hook(state, r, shot)`` after each round's last op
        for bond-profile diagnostics. A :class:`BondAbortError` propagates
        (the runner owns the orderly-stop bookkeeping).
        """
        if sched is None:
            raise ValueError(
                "PepsSampler requires an explicit compiled schedule with "
                "within-cycle streams; circuit parsing belongs to the frontend")
        if str(spec.dtype) != "c128":
            raise ValueError(
                "PepsSampler executes torch complex128 only; RunSpec.dtype must "
                f"be 'c128' so the emitted header matches the carrier (got "
                f"{spec.dtype!r})")
        if self.device.type != "cuda":
            raise RuntimeError(
                "PepsSampler device must be CUDA "
                f"(got {self.device})")
        if not torch.cuda.is_available():
            raise RuntimeError("PepsSampler requires CUDA")
        if str(spec.arm).upper() == "C":
            raise ValueError("arm C is unsupported by this trajectory; arm A is required")
        if not sched.within_cycle_streams:
            raise ValueError(
                "PepsSampler (within-cycle) requires sched.within_cycle_streams "
                "(a MULTI-ROUND source circuit's interior streams). Attach them via "
                "sched.with_within_cycle_streams(parse_within_cycle_streams(r10)).")

        leak_t, _leak_ev = self._host.build_within_cycle_leak(spec)  # builder enforces CPTP
        marsh = self._host.marshal_within_cycle(sched, leak_t, R=spec.R)
        n_data = int(marsh.n_data)
        R = int(marsh.R)
        leak_kraus = [leak_t[k] for k in range(leak_t.shape[0])]

        codestate = build_codestate_peps(sched, spec.m, device=str(self.device))
        gate_table = {SV_GATE_IDS[name]: qutrit_gate(name, self.device)
                      for name in SV_GATE_NAMES}

        stab_supp = marsh.stab_supp.detach().cpu().numpy()
        stab_isx = marsh.stab_supp_isx.detach().cpu().numpy()
        stab_len = marsh.stab_supp_len.detach().cpu().numpy()
        log_sites = [int(x) for x in marsh.log_supp.detach().cpu().numpy().tolist()]
        log_isx = [int(x) for x in marsh.log_supp_isx.detach().cpu().numpy().tolist()]

        b_eff = 0.5 if str(spec.readout_conv) == "half" else float(spec.b)
        n_stab = int(marsh.n_stab)
        N = int(spec.N)
        syndromes = np.zeros((N, n_stab * R), dtype=np.uint8)
        flips = np.zeros((N,), dtype=np.uint8)
        ledgers: list[list] = []

        for shot in range(N):
            # Per-shot RNG keyed by (base_seed, shot), matching the reference stream.
            rng = np.random.default_rng((int(spec.base_seed), shot))
            hook = None
            if round_hook is not None:
                def hook(st, r, _shot=shot):
                    round_hook(st, r, _shot)
            bits, obs, _tbits, final = run_trajectory(
                codestate, marsh, leak_kraus, gate_table, stab_supp, stab_isx,
                stab_len, log_sites, log_isx, str(spec.arm).upper(), float(spec.b),
                b_eff, int(spec.m), policy, n_data, R, rng,
                R_n=R_n, R_x=R_x, fit_seed=fit_seed, d_abort=d_abort,
                cross_route_pred=cross_route_pred, chib_pred=chib_pred, chi_b=chi_b,
                round_hook=hook)
            syndromes[shot, :] = np.asarray(bits, dtype=np.uint8)
            flips[shot] = np.uint8(obs)
            ledgers.append(final.ledger)

        packed = pack_raw_syndrome_shots(syndromes, flips)
        header = self._host.build_header(spec, marsh, sched)
        header["backend"] = "peps_singlewire/quimb"
        header["compiled_semantics"] = "compiled/data-register"
        header["peps_policy"] = {
            "mode": policy.mode,
            "eps_spike": policy.eps_spike,
            "D_cap": policy.D_cap,
            "W_max": policy.W_max,
        }
        header["peps_R_n"] = R_n
        header["peps_R_x"] = R_x
        header["peps_fit_seed"] = int(fit_seed)
        header["peps_d_abort"] = d_abort

        bits_per_shot = n_stab * R
        out_path = None
        header_path = None
        if spec.out_path is not None:
            import json
            from pathlib import Path
            out_path = Path(spec.out_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            header_path = out_path.with_suffix(out_path.suffix + ".header.json")
            header_path.write_text(json.dumps(header, indent=2))
            with open(out_path, "wb") as fh:
                fh.write(np.ascontiguousarray(packed).tobytes())

        shotset = PackedShotBatch(
            header=header,
            path=out_path,
            header_path=header_path,
            n_shots=N,
            syndrome_bits_per_shot=bits_per_shot,
            diag={"peps_n_ledgers": len(ledgers)},
            shots=(packed if materialize else None),
        )
        return shotset, ledgers

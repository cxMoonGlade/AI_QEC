from __future__ import annotations

r"""Rung-1 PEPO engine — dynamics [builder A2].

Contract: ``docs/nonpauli_teacher/pepo_engine_rung1_contract.md`` (v4.2) §3 rows
``apply_token_stream`` / ``apply_postmeasure`` / ``stab_channel_tt`` /
``nonselective_round`` / ``ntu_truncate`` (+ the pinned ``gap_rank`` rule);
governing registration ``docs/nonpauli_teacher/pepo_d5d7_carrier_prereg.md`` (v2.4).
Scope label (C10/S10): everything here acts on the COMPILED / DATA-REGISTER record
law (stabilizer readout as direct Lüders parity channels on the data qutrits).

The state is a :class:`~..pepo.layout.PepoState`: a quimb ``TensorNetwork`` of one
rank<=5 site tensor per data qutrit, physical leg = the FUSED d^2 = 9 vectorized
index (ket (x) bra, ROW-MAJOR vec: fused index ``k = 3*t_ket + t_bra`` — pinned;
contract §2), tag ``Q{pos}`` / ind ``k{pos}``, virtual bonds on the (u', v') grid
edges. torch complex128 everywhere; devices are passed in, never guessed.

Fused-leg superoperator convention (row-major vec): ``vec(A rho B) =
(A (x) B^T) vec(rho)``, so a unitary conjugation ``rho -> U rho U^dag`` is the
9x9 superop ``U (x) conj(U)`` and a Kraus channel is ``sum_k K_k (x) conj(K_k)``
(contract §3 row ``apply_token_stream``).

Referee (equivalence target, NEVER imported for certification):
``carrier/exact/qutrit_dm.py`` — ``apply_within_cycle_premeasure`` /
``apply_within_cycle_postmeasure`` (F1) and ``_povm_diag_weight`` /
``project_stabilizer`` (F2). The single-qutrit ``H``/``X``/``Y`` matrices below are
the SAME pinned definitions (computational {|0>,|1>} block, leaked |2> inert) —
defined locally so the engine shares no code path with its referee.

NTU truncation ports the rung-0 metric seed
``outputs/nonpauli_teacher/pepo_rung0_ntu_metric_unit.py`` (fixed revision, F6:
metric ROWS = the BRA insertion, eps = v^H g v; content_hash b5f4f834...) with the
cluster adapted to the ACTUAL PEPO neighborhood of the truncated bond: the two
bond sites (QR-isometrized) + their PRESENT grid neighbors, parallel bonds
included, every external leg traced bra-ket. Where a grid edge has NO neighbor
(patch boundary), there simply is no leg / no neighbor double — tracing an
absent environment is contracting with the IDENTITY on that leg, i.e. the
boundary environment contribution is the identity (documented per the brief).
"""

import math
from dataclasses import dataclass, field

import torch
import quimb.tensor as qtn

from ...numerics import NUMERICAL_ZERO

CDTYPE = torch.complex128
RDTYPE = torch.float64

#: NTU alternating-pinv loop constants (class (c) design constants, documented —
#: the seed's C5 verified a single pinv step against the closed dense referee;
#: the engine alternates both sides until the eps improvement stalls).
_NTU_MAX_SWEEPS = 20
_NTU_REL_STOP = 1e-12
_NTU_PINV_RTOL = 1e-12  # the seed's pinv rtol


# --------------------------------------------------------------------------- #
# Pinned single-qutrit gate matrices (F1; leaked |2> inert)                    #
# --------------------------------------------------------------------------- #
def _qutrit_gate(name: str, device) -> torch.Tensor:
    """The pinned single-qutrit frame gates on the computational ``{|0>,|1>}``
    block with the leaked level ``|2>`` inert (identical formulas to the referee's
    ``qudit_hadamard`` / ``single_qudit_gate`` — defined locally, F1)."""
    m = torch.zeros((3, 3), dtype=CDTYPE, device=device)
    if name == "H":
        inv2 = 1.0 / (2.0 ** 0.5)
        m[0, 0] = inv2
        m[0, 1] = inv2
        m[1, 0] = inv2
        m[1, 1] = -inv2
    elif name == "X":
        m[0, 1] = 1.0
        m[1, 0] = 1.0
    elif name == "Y":
        m[0, 1] = -1.0j
        m[1, 0] = 1.0j
    else:
        raise ValueError(f"unsupported pinned qutrit gate {name!r}")
    m[2, 2] = 1.0
    return m


def _gate_superop(U: torch.Tensor) -> torch.Tensor:
    """9x9 fused-leg superop of ``rho -> U rho U^dag`` (row-major vec):
    ``U (x) conj(U)``."""
    return torch.kron(U, U.conj())


def _kraus_superop(kraus) -> torch.Tensor:
    """9x9 fused-leg superop of the CPTP channel ``rho -> sum_k K_k rho K_k^dag``
    (row-major vec): ``sum_k K_k (x) conj(K_k)``.

    C4 (constraint ledger): Kraus completeness ``sum_k K_k^dag K_k = I`` is
    asserted to 1e-12 at every build (a dropped Kraus element trips it).
    """
    ks = torch.stack([torch.as_tensor(k) for k in kraus])
    if ks.shape[-2:] != (3, 3):
        raise ValueError(f"each single-qutrit Kraus must be (3, 3), got {tuple(ks.shape[-2:])}")
    ks = ks.to(CDTYPE)
    comp = torch.einsum("kba,kbc->ac", ks.conj(), ks)
    eye = torch.eye(3, dtype=CDTYPE, device=ks.device)
    resid = float((comp - eye).abs().max())
    assert resid <= 1e-12, f"C4: Kraus completeness violated (max|sum K^dag K - I| = {resid:.3e})"
    sop = torch.zeros((9, 9), dtype=CDTYPE, device=ks.device)
    for k in range(ks.shape[0]):
        sop = sop + torch.kron(ks[k], ks[k].conj())
    return sop


# --------------------------------------------------------------------------- #
# Site-tensor access + single-site fused superop application                   #
# --------------------------------------------------------------------------- #
def _site_tensor(state, pos: int):
    """The unique site tensor tagged ``Q{pos}``."""
    ts = state.tn.select_tensors(f"Q{int(pos)}")
    if len(ts) != 1:
        raise RuntimeError(f"expected exactly one tensor tagged Q{pos}, found {len(ts)}")
    return ts[0]


def _apply_fused_superop(state, pos: int, sop: torch.Tensor) -> None:
    """Contract a 9x9 superop onto the fused physical leg ``k{pos}``.

    Single-site by construction: bond dims are ASSERTED unchanged (contract §3
    row ``apply_token_stream``: "Single-site: NO bond change (assert)").
    """
    t = _site_tensor(state, pos)
    kname = f"k{int(pos)}"
    ax = t.inds.index(kname)
    shape_before = tuple(t.data.shape)
    data = torch.movedim(torch.tensordot(sop, t.data, dims=([1], [ax])), 0, ax)
    assert tuple(data.shape) == shape_before, (
        f"single-site superop changed the tensor shape at Q{pos}: "
        f"{shape_before} -> {tuple(data.shape)}")
    t.modify(data=data.contiguous())


# --------------------------------------------------------------------------- #
# F1 within-cycle token streams                                                #
# --------------------------------------------------------------------------- #
def apply_token_stream(state, streams: dict, leak_kraus) -> None:
    """Apply the per-position PRE-measurement within-cycle token streams (F1,
    VERBATIM semantics of ``QutritDM.apply_within_cycle_premeasure``).

    Per position, tokens IN ORDER, stop at ``M``: ``H`` -> qutrit-Hadamard
    superop, ``X`` -> X superop, ``LEAK`` -> the Kraus-sum superop
    ``sum_k K_k (x) conj(K_k)`` on the fused leg, ``Y`` IGNORED pre-M (post-M
    frame), any other unknown token RAISES. Single-qutrit ops on distinct sites
    commute, so replaying each position's stream sequentially equals the true
    global interleaving (the referee's own argument).
    """
    dev = _site_tensor(state, next(iter(sorted(streams)))).data.device if streams else None
    leak_sop = None
    gate_sops: dict[str, torch.Tensor] = {}
    for pos in sorted(streams):
        toks = streams[pos]
        site = int(pos)
        for tok in toks:
            if tok == "M":
                break
            if tok == "LEAK":
                if leak_sop is None:
                    leak_sop = _kraus_superop([torch.as_tensor(k).to(device=dev) for k in leak_kraus])
                _apply_fused_superop(state, site, leak_sop)
            elif tok in ("H", "X"):
                if tok not in gate_sops:
                    gate_sops[tok] = _gate_superop(_qutrit_gate(tok, dev))
                _apply_fused_superop(state, site, gate_sops[tok])
            elif tok == "Y":
                continue  # post-M frame: applied by apply_postmeasure
            else:
                raise ValueError(
                    f"within-cycle pre-measure: unknown token {tok!r} at site {site}")


def apply_postmeasure(state, streams: dict, terminal: bool = False) -> None:
    """Apply the per-position POST-measurement frame (the transversal ``Y``; F1,
    VERBATIM semantics of ``QutritDM.apply_within_cycle_postmeasure``).

    ``terminal=True`` skips everything (the terminal round ends in the terminal
    data readout). Only tokens AFTER the ``M`` marker are considered. RAISE SET
    PINNED (contract §3, v2 fix): post-M ``X`` / ``H`` / ``LEAK`` raise; any
    OTHER unknown post-M token is SILENTLY IGNORED (the referee does not raise
    on arbitrary post-M tokens — a raises-on-unknown killer would split engine
    vs referee).
    """
    if terminal:
        return
    y_sop = None
    for pos in sorted(streams):
        toks = streams[pos]
        site = int(pos)
        seen_m = False
        for tok in toks:
            if tok == "M":
                seen_m = True
                continue
            if not seen_m:
                continue
            if tok == "Y":
                if y_sop is None:
                    dev = _site_tensor(state, site).data.device
                    y_sop = _gate_superop(_qutrit_gate("Y", dev))
                _apply_fused_superop(state, site, y_sop)
            elif tok in ("X", "H", "LEAK"):
                raise ValueError(
                    f"within-cycle post-measure: unexpected token {tok!r} after M at site "
                    f"{site} (only the transversal Y is expected post-M for d3 XZZX)")
            # any other token: silently ignored (pinned raise set — see docstring)


# --------------------------------------------------------------------------- #
# Stabilizer channel: exact numeric TT of the fused diagonal (F2)              #
# --------------------------------------------------------------------------- #
@dataclass
class StabTT:
    """The exact numeric tensor train of one stabilizer-measurement fused-leg
    diagonal superoperator along the plaquette path (contract §3 row
    ``stab_channel_tt``).

    ``path``    ordered grid-adjacent engine positions through the support;
    ``cores``   ``w`` TT cores, core ``p`` of shape ``(r_{p-1}, 9, r_p)`` with
                the boundary ranks squeezed out at application time
                (``r_0 = r_w = 1`` stored explicitly);
    ``x_sites`` support sites with Pauli ``X`` — the single-site H superop
                sandwich applied OUTSIDE the TT (F2);
    ``outcome`` the syndrome bit ``s`` in {0, 1}; ``-1`` marks the NON-SELECTIVE
                branch-sum diagonal ``D_0 + D_1`` built by
                :func:`nonselective_round`;
    ``ranks``   the MEASURED TT bond ranks (logged per contract).
    """

    path: tuple
    cores: list = field(default_factory=list)
    x_sites: tuple = ()
    outcome: int = 0
    b: float = 0.0
    arm: str = "A"
    ranks: tuple = ()


def _leaked_weight(b: float, arm: str) -> float:
    """The per-site LEAKED parity weight ``d_q(leaked)`` (F2, the normative
    ``_povm_diag_weight`` b/arm table): arm A/C -> ``1 - 2b``; B1 -> ``+1``;
    B2 -> ``-1``."""
    a = str(arm).upper()
    if a in ("A", "C"):
        bb = float(b)
        if not 0.0 <= bb <= 1.0:
            raise ValueError(f"readout bias b must be a probability in [0, 1] (got {bb})")
        return 1.0 - 2.0 * bb
    if a == "B1":
        return 1.0
    if a == "B2":
        return -1.0
    raise ValueError(f"unknown measurement arm {arm!r} (expected A, C, B1 or B2)")


def _fused_stab_diag(path, outcome: int, b: float, arm: str, device) -> torch.Tensor:
    """The fused diagonal ``D[k_1..k_w] = sqrt(e)[t_1..t_w] * sqrt(e)[t'_1..t'_w]``
    of ``sqrt(E_s) . rho . sqrt(E_s)`` over the support, axes in PATH order,
    per-site fused index ``k = 3*t_ket + t_bra`` (row-major, pinned).

    ``e_i = 1/2 (1 + (-1)^s prod_q d_q)`` with ``d_q = +1 (t=0), -1 (t=1),
    d_leaked (t=2)`` — the F2 formula VERBATIM. Every site is read as a Z
    parity here: X supports are H-rotated OUTSIDE the TT (F2).
    """
    w = len(path)
    d2 = _leaked_weight(b, arm)
    dvec = torch.tensor([1.0, -1.0, d2], dtype=RDTYPE, device=device)
    prod = dvec
    for _ in range(w - 1):
        prod = prod[..., None] * dvec  # axes accumulate in path order
    sign = 1.0 if (int(outcome) & 1) == 0 else -1.0
    e = 0.5 * (1.0 + sign * prod)                     # (3,)*w
    sq = torch.sqrt(torch.clamp(e, min=0.0))
    v = sq.reshape(3 ** w)
    dm = v[:, None] * v[None, :]                      # [ket, bra] joint
    dm = dm.reshape([3] * w + [3] * w)
    perm = []
    for p in range(w):
        perm += [p, w + p]                            # interleave (t_p, t'_p)
    dm = dm.permute(*perm).reshape([9] * w)           # fused k_p = 3 t_p + t'_p
    return dm.to(CDTYPE)


def _tt_svd(diag: torch.Tensor):
    """EXACT TT decomposition of a ``(9,)*w`` diagonal by sequential SVD;
    candidate values with ``sigma <= 1e-12 * sigma_1`` (per-SVD) dropped
    (contract §3 pin). Returns ``(cores, ranks)`` with core ``p`` of shape
    ``(r_{p-1}, 9, r_p)``."""
    w = diag.dim()
    cores = []
    ranks = []
    m = diag.reshape(9, -1)
    rl = 1
    for _ in range(w - 1):
        U, S, Vh = torch.linalg.svd(m, full_matrices=False)
        if float(S[0]) <= 0.0:
            r = 1
        else:
            r = max(1, int((S > NUMERICAL_ZERO * S[0]).sum()))
        cores.append(U[:, :r].reshape(rl, 9, r).contiguous())
        ranks.append(r)
        m = (S[:r, None].to(CDTYPE) * Vh[:r]).reshape(r * 9, -1)
        rl = r
    cores.append(m.reshape(rl, 9, 1).contiguous())
    return cores, tuple(ranks)


def _tt_rank_bounds(w: int) -> tuple:
    """The DERIVED per-bond TT rank bound ``(2 min(w_L, w_R) + 1)^2`` (v2 B1:
    the ket (x) bra squaring) — (9, 25, 9) for w=4, (9,) for w=2."""
    return tuple((2 * min(p, w - p) + 1) ** 2 for p in range(1, w))


def _assert_path_adjacent(layout, path) -> None:
    """Defensive: consecutive path sites must be grid-adjacent (|du|+|dv| == 1)."""
    for a, bpos in zip(path, path[1:]):
        ua, va = layout.grid[a]
        ub, vb = layout.grid[bpos]
        assert abs(ua - ub) + abs(va - vb) == 1, (
            f"plaquette path not grid-adjacent at ({a}, {bpos})")


def stab_channel_tt(paulis: dict, outcome: int, b: float, arm: str, layout, device: str) -> StabTT:
    """The EXACT numeric TT of the diagonal fused-leg superoperator of
    ``sqrt(E_s) . rho . sqrt(E_s)`` over the support (contract §3 row, F2).

    Builds the ``3^w`` diagonal ``e_i`` from the F2 formula, takes the square
    root, forms the fused diagonal ``sqrt(e_i) sqrt(e_j)``, and TT-decomposes it
    EXACTLY (SVD; sigma <= 1e-12 sigma_1 dropped) along
    ``layout.plaquette_path(paulis)``.

    RANK ASSERTS (domain-pinned, v3): for ``arm in {A, C}`` AND
    ``b not in {0, 0.5, 1}`` the TT bond rank must EQUAL the derived bound
    ``(2 min(w_L, w_R) + 1)^2`` at each bond — (9, 25, 9) for w=4, (9,) for
    w=2 (the registered p1c evidence point b=0.9). OUTSIDE that domain (b in
    {0, 0.5, 1}, arms B1/B2) the product classes collapse and the assert is
    ``rank <= the domain bound``, never ``==``. Measured ranks are carried on
    the returned :class:`StabTT` (logged by the callers).

    X supports are NOT folded into the TT: they are recorded on
    ``StabTT.x_sites`` and sandwiched with single-site H superops by
    :func:`apply_stab_branch` (F2 — H-rotation outside the TT; leaked levels
    H-inert, so the leaked rows are basis-independent).
    """
    dev = torch.device(device)
    for s, pp in paulis.items():
        if str(pp).upper() not in ("X", "Z"):
            raise ValueError(f"stabilizer support must be X/Z (XZZX), got {pp!r} at site {s}")
    if int(outcome) not in (0, 1):
        raise ValueError(f"outcome must be 0 or 1 (got {outcome})")
    path = tuple(int(s) for s in layout.plaquette_path(paulis))
    assert len(path) == len(paulis) >= 2, (path, paulis)
    _assert_path_adjacent(layout, path)
    w = len(path)

    diag = _fused_stab_diag(path, outcome, b, arm, dev)
    cores, ranks = _tt_svd(diag)
    bounds = _tt_rank_bounds(w)
    in_domain = (str(arm).upper() in ("A", "C")
                 and not any(abs(float(b) - v) <= NUMERICAL_ZERO for v in (0.0, 0.5, 1.0)))
    if in_domain:
        assert ranks == bounds, (
            f"stab TT rank mismatch (arm={arm}, b={b}, w={w}): measured {ranks}, "
            f"derived bound {bounds} (v2 B1: (2 min(w_L,w_R)+1)^2 — equality pinned "
            f"on the arm A/C, b not in {{0, 0.5, 1}} domain)")
    else:
        assert all(r <= bd for r, bd in zip(ranks, bounds)), (
            f"stab TT rank above the domain bound (arm={arm}, b={b}): {ranks} vs {bounds}")
    x_sites = tuple(sorted(int(s) for s, pp in paulis.items() if str(pp).upper() == "X"))
    return StabTT(path=path, cores=cores, x_sites=x_sites, outcome=int(outcome),
                  b=float(b), arm=str(arm).upper(), ranks=ranks)


# --------------------------------------------------------------------------- #
# Branch application (grows support-path bonds; NO truncation inside)          #
# --------------------------------------------------------------------------- #
def _leak_dephase_superop(device) -> torch.Tensor:
    """Arm-C leak-flag dephase as a PER-SITE fused-leg diagonal mask (contract
    v4.2 ARM-C DEPHASE paragraph): entry 1 iff ``(t_ket >= 2) == (t_bra >= 2)``,
    i.e. the cross-leak-sector fused entries are zeroed. The product of these
    per-site masks over the support EQUALS the referee's joint dephase
    ``QutritDM._leak_flag_dephase`` (``rho[i,j] -> 0`` iff ANY support site's
    leak flags differ), and the mask is H-invariant (H does not touch the
    leaked level), matching the referee's basis-aligned claim. Single-site
    diagonal — NO bond change."""
    flag = torch.tensor([0, 0, 1], dtype=torch.long, device=device)
    keep = (flag[:, None] == flag[None, :]).reshape(9)  # fused k = 3 t_ket + t_bra
    return torch.diag(keep.to(CDTYPE))


def _insert_core(t, kname: str, core: torch.Tensor, lname, rname) -> None:
    """Multiply TT core ``core[(l), k, (r)]`` elementwise onto the fused leg
    ``kname`` of tensor ``t``, appending the new TT bond legs ``lname`` /
    ``rname`` (``None`` at the path endpoints — the dim-1 boundary rank is
    squeezed so no dangling index is ever created)."""
    ax = t.inds.index(kname)
    d = torch.movedim(t.data, ax, -1)                      # (..., 9)
    out = torch.einsum("...k,lkr->...lrk", d, core)        # (..., rl, rr, 9)
    inds = [i for i in t.inds if i != kname]
    if lname is None:
        assert core.shape[0] == 1, "non-trivial left rank at the path start"
        out = out[..., 0, :, :]
    else:
        inds.append(lname)
    if rname is None:
        assert core.shape[2] == 1, "non-trivial right rank at the path end"
        out = out[..., 0, :]
    else:
        inds.append(rname)
    inds.append(kname)
    t.modify(data=out.contiguous(), inds=tuple(inds))


def apply_stab_branch(state, stab_tt: StabTT) -> None:
    """Apply one stabilizer-channel TT to the state (contract §3): H-superop
    sandwich on the X supports (OUTSIDE the TT), TT cores multiplied onto the
    fused legs along the support path, TT bonds fused with the pre-existing
    grid bonds. GROWS the support-path bonds by the TT ranks; NO truncation
    inside (the caller truncates via :func:`ntu_truncate`).

    ARM-C DEPHASE (contract v4.2): for ``arm == 'C'`` the referee's leak-flag
    dephase (:func:`_leak_dephase_superop`) is applied to every SUPPORT site
    BEFORE the TT — the pinned ORDER is dephase-then-E_s, matching
    ``QutritDM.project_stabilizer`` (dephase after the X-support H rotation,
    before the diagonal E_s update). Single-site diagonal mask: no bond change
    (asserted inside :func:`_apply_fused_superop`)."""
    dev = _site_tensor(state, stab_tt.path[0]).data.device
    h_sop = _gate_superop(_qutrit_gate("H", dev))
    for pos in stab_tt.x_sites:
        _apply_fused_superop(state, pos, h_sop)

    if str(stab_tt.arm).upper() == "C":
        dep_sop = _leak_dephase_superop(dev)
        for pos in stab_tt.path:
            _apply_fused_superop(state, pos, dep_sop)  # single-site: bond-change asserted absent

    w = len(stab_tt.path)
    tt_bonds = [qtn.rand_uuid() for _ in range(w - 1)]
    for p, pos in enumerate(stab_tt.path):
        t = _site_tensor(state, pos)
        lname = tt_bonds[p - 1] if p > 0 else None
        rname = tt_bonds[p] if p < w - 1 else None
        _insert_core(t, f"k{int(pos)}", stab_tt.cores[p].to(device=dev), lname, rname)
    # fuse each new TT bond with the pre-existing grid bond of the same edge
    # (a path edge with no pre-existing bond simply keeps the TT bond).
    state.tn.fuse_multibonds(inplace=True)

    for pos in stab_tt.x_sites:
        _apply_fused_superop(state, pos, h_sop)


# --------------------------------------------------------------------------- #
# Pinned gap rule (v4.1 — gate-load-bearing; implemented LITERALLY)            #
# --------------------------------------------------------------------------- #
def gap_rank(sigma: torch.Tensor, D_cap: int):
    """The v4.1 window-bound gap rule, VERBATIM (contract §3 ``ntu_truncate``
    row; applies to GLOBAL spectrum reads G1.3/G1.6 and ledger effective-rank
    reporting ONLY):

      candidates = ``k <= D_cap`` with ``sigma_k > 1e-12 sigma_1`` (the sigma_k
      guard — a rank-deficient window must not qualify via inf/inf; if NO k in
      the window passes it, effective rank = the count of ``sigma > floor``);
      ``ratio(k) = sigma_k / sigma_{k+1}``, with ``ratio(k) := inf`` when
      ``sigma_{k+1} <= 1e-12 sigma_1`` (or absent); qualifying = ``ratio(k) >=
      10``; pick the LARGEST qualifying ``k <= D_cap``; none qualifying =>
      effective rank = ``D_cap`` + CAP_BINDING. The window ``k <= D_cap`` binds
      everything; inf-ratios arise only inside it. The winning ratio is always
      returned (logged by callers).

    ``sigma`` is the UNSQUARED singular-value spectrum (units table). Returns
    ``(rank, winning_ratio, cap_binding)``. Pinned edge semantics (the rule is
    silent; documented here, flagged in the build report): in the sigma_k-guard
    fallback the ratio is returned as 0.0 and cap_binding False; in the
    CAP_BINDING case the returned ratio is the LARGEST ratio observed among the
    candidates (all < 10).
    """
    D_cap = int(D_cap)
    s = torch.as_tensor(sigma).detach()
    s = s.real.to(RDTYPE).flatten()
    s, _ = torch.sort(s, descending=True)
    n = int(s.numel())
    if n == 0 or float(s[0]) <= 0.0:
        return 0, 0.0, False
    floor = NUMERICAL_ZERO * float(s[0])
    kmax = min(D_cap, n)
    candidates = [k for k in range(1, kmax + 1) if float(s[k - 1]) > floor]
    if not candidates:
        return int((s > floor).sum()), 0.0, False
    best_k = None
    best_k_ratio = 0.0
    max_ratio = 0.0
    for k in candidates:
        nxt = float(s[k]) if k < n else 0.0
        ratio = math.inf if nxt <= floor else float(s[k - 1]) / nxt
        max_ratio = max(max_ratio, ratio)
        if ratio >= 10.0 and (best_k is None or k > best_k):
            best_k, best_k_ratio = k, ratio
    if best_k is not None:
        return int(best_k), float(best_k_ratio), False
    return D_cap, float(max_ratio), True


# --------------------------------------------------------------------------- #
# NTU truncation (the rung-0 metric seed, adapted to the live neighborhood)    #
# --------------------------------------------------------------------------- #
def _neighbors(layout, pos: int) -> list:
    """PRESENT grid neighbors of ``pos`` (patch boundary => fewer neighbors —
    the absent-edge environment is the identity, see module docstring)."""
    u, v = layout.grid[int(pos)]
    out = []
    for du, dv in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        q = layout.pos_at.get((u + du, v + dv))
        if q is not None:
            out.append(int(q))
    return out


def _pos_of_tensor(t) -> int:
    """Engine position from the ``Q{pos}`` site tag."""
    for tag in t.tags:
        if isinstance(tag, str) and tag.startswith("Q") and tag[1:].isdigit():
            return int(tag[1:])
    raise RuntimeError(f"site tensor without a Q{{pos}} tag: tags={tuple(t.tags)}")


def _qr_split(t, bond: str):
    """QR-isometrize a site tensor against ``bond``: ``T = Q . R`` with ``Q`` an
    isometry over ALL non-bond legs (phys included — the seed's Q_A row group)
    and ``R (q, r)`` the bond matrix. Returns ``(Q2d, R, rest_inds, rest_dims)``."""
    ax = t.inds.index(bond)
    d = torch.movedim(t.data, ax, -1)
    rest_dims = tuple(d.shape[:-1])
    r = int(d.shape[-1])
    mat = d.reshape(-1, r)
    Qm, Rm = torch.linalg.qr(mat, mode="reduced")     # (rest, q), (q, r)
    rest_inds = tuple(i for i in t.inds if i != bond)
    return Qm, Rm, rest_inds, rest_dims


def _gauge_cut_pair(t1, t2, ind: str, width: int):
    """Plain SVD gauge-cut of the shared ``ind`` between two cluster COPY tensors
    (qtn.Tensor) down to ``width`` — the metric-side v4.3 env bounding. Returns the
    two replacement tensors and the discarded squared-sigma weight."""
    Q1, R1, ri1, rd1 = _qr_split(t1, ind)
    Q2, R2, ri2, rd2 = _qr_split(t2, ind)
    X = R1 @ R2.mT
    U, S, Vh = torch.linalg.svd(X, full_matrices=False)
    s_sq = (S * S).to(RDTYPE)
    tot = float(s_sq.sum())
    k = min(int(width), int(S.numel()))
    sqrt_s = torch.sqrt(S[:k]).to(CDTYPE)
    n1 = qtn.Tensor(((Q1 @ U[:, :k]) * sqrt_s).reshape(*rd1, k), inds=ri1 + (ind,))
    n2 = qtn.Tensor(((Q2 @ Vh[:k].mT) * sqrt_s).reshape(*rd2, k), inds=ri2 + (ind,))
    disc = float(s_sq[k:].sum()) / tot if tot > 0.0 else 0.0
    return n1, n2, disc


def _cluster_metric(state, layout, pos_a: int, pos_b: int, bond: str,
                    QA: torch.Tensor, QB: torch.Tensor,
                    rest_inds_a, rest_dims_a, rest_inds_b, rest_dims_b,
                    D_cap: int) -> tuple:
    """The NTU metric ``g`` on the insertion product space, ROWS = the BRA
    insertion (F6, the rung-0 C4-caught convention:
    ``g[(IJ),(ij)] = <cluster(IJ)|cluster(ij)>``; ``eps = v^H g v``).

    Cluster = the two QR-isometries (phys legs inside their row groups) + the
    PRESENT grid neighbors of both sites (the seed's L/UA/DA/UB/DB/R pattern,
    generalized): the bonds PARALLEL to the truncated bond (neighbor-neighbor
    edges) are kept INSIDE the cluster — the NTU-vs-SU feature; every leg that
    leaves the cluster (neighbor outer bonds + all phys legs) is traced
    bra-ket. A missing neighbor (patch boundary) contributes the IDENTITY
    environment: there is no leg to close, which IS the identity contraction.

    Built as an explicit two-layer (ket + conj/bra) quimb network and
    contracted with open insertion legs; the staged Fig.-4 double-tensor object
    is identical (the seed verified structured == dense at ~5e-16).

    v4.3 ENV BOUNDING (2026-07-10 first-execution fix): every internal cluster
    bond with dim > ``D_cap`` is gauge-cut to ``D_cap`` on the cluster COPY
    (the state is untouched) BEFORE doubling. Rationale: the doubled cluster
    squares every internal bond, so a core site carrying two 25–64-dim bonds
    yields ket⊗bra intermediates of (25·64·64)² ≈ 1e10 elements (~168 GB) —
    byte-infeasible regardless of contraction order (measured: a 3/3
    deterministic WSL2 'device not ready' at ~20-GiB allocation attempts). In
    literature NTU (Dziarmaga 2107.06635) the cluster ALWAYS sees neighbors at
    D — two-site gates are truncated immediately; our stab TT grows the whole
    path at once, so the D-bounded cluster must be restored by hand. The
    metric becomes a controlled approximation of the (infeasible) raw-width
    cluster metric — NTU is itself a finite-cluster approximation; class (c)
    design rule with (a) ledger (env cut count + max discarded returned to the
    ntu_truncate ledger entry), empirically bounded by the G1.2/G1.4
    record-faithfulness gates. Returns ``(g, env_stats)``.
    """
    ii, jj, Ib, Jb = (qtn.rand_uuid() for _ in range(4))
    kets = []
    qa = int(QA.shape[1])
    qb = int(QB.shape[1])
    kets.append(qtn.Tensor(QA.reshape(*rest_dims_a, qa), inds=rest_inds_a + (ii,)))
    kets.append(qtn.Tensor(QB.reshape(*rest_dims_b, qb), inds=rest_inds_b + (jj,)))
    nb_pos = sorted(set(_neighbors(layout, pos_a) + _neighbors(layout, pos_b))
                    - {int(pos_a), int(pos_b)})
    for q in nb_pos:
        tq = _site_tensor(state, q)
        kets.append(qtn.Tensor(tq.data, inds=tq.inds))
    # internal cluster bonds = inds shared by >= 2 ket tensors (A/B-neighbor
    # bonds + the parallel neighbor-neighbor bonds); everything else is traced.
    counts: dict[str, int] = {}
    for kt in kets:
        for ind in kt.inds:
            counts[ind] = counts.get(ind, 0) + 1
    internal = {ind for ind, c in counts.items() if c >= 2}
    # v4.3 env bounding (see docstring): gauge-cut oversize internal bonds on
    # the COPY cluster; ii/jj are insertion legs (width already <= 4*D_cap by
    # the v4.2 insertion precut) and are never touched.
    env_cuts = 0
    env_disc_max = 0.0
    for ind in sorted(internal):
        dim = next(int(kt.shape[kt.inds.index(ind)]) for kt in kets if ind in kt.inds)
        if dim <= int(D_cap):
            continue
        i1, i2 = [k for k, kt in enumerate(kets) if ind in kt.inds]
        n1, n2, disc = _gauge_cut_pair(kets[i1], kets[i2], ind, int(D_cap))
        kets[i1], kets[i2] = n1, n2
        env_cuts += 1
        env_disc_max = max(env_disc_max, disc)
    ren = {ind: qtn.rand_uuid() for ind in internal}
    ren[ii] = Ib
    ren[jj] = Jb
    bras = [qtn.Tensor(kt.data.conj(), inds=tuple(ren.get(ind, ind) for ind in kt.inds))
            for kt in kets]
    # optimize="greedy": deterministic path (no cotengra random hyper-sampling) —
    # 2026-07-10 first-execution fix; cluster dims are bounded (env <= D_cap,
    # insertion <= 4*D_cap), so greedy is both safe and reproducible.
    g4 = qtn.TensorNetwork(kets + bras).contract(output_inds=(Ib, Jb, ii, jj),
                                                 optimize="greedy")
    g4.transpose_(Ib, Jb, ii, jj)
    g = g4.data.reshape(qa * qb, qa * qb)
    g = 0.5 * (g + g.conj().mT)  # light Hermitian symmetrization (g is PSD Hermitian)
    return g, {"env_gauge_cuts": int(env_cuts),
               "env_gauge_discarded_max": float(env_disc_max)}


def svd_precut_bond(state, bond: str, width: int) -> dict:
    """Plain LOCAL SVD gauge-cut of one bond to ``width`` — NO cluster metric.

    v4.3 FIRST-EXECUTION amendment (2026-07-10): the within-round support-path
    truncation runs this bounded-width PRE-PASS over every grown path bond
    BEFORE the NTU refinement pass. Rationale (Stage-5 first execution — a 3/3
    deterministic torch failure at the g4 cluster contraction): the NTU metric
    cluster doubles every not-yet-truncated NEIGHBOR bond (grown up to 25·D),
    so a neighbor ket⊗bra transfer object costs (25·D)^4 · 16 B ≈ 410 GB at
    D = 16 — byte-infeasible REGARDLESS of contraction order (the v4.2 budget
    counted site-tensor storage, not the metric-cluster doubles). The pre-pass
    bounds every cluster bond to ``width`` (= 4·D_cap at the call sites,
    preserving the v4.2 4× NTU headroom; transfer objects then
    ≤ (4·D_cap)^4 · 16 B ≈ 268 MB at D_cap = 16). The cut itself is the plain
    truncated SVD of the pair insertion — the LOCAL Frobenius optimum, the same
    drop convention as :func:`ntu_truncate`'s exact path, i.e. the v4.2
    insertion pre-compression promoted to a state-side pass. Class (c) design
    rule with (a) ledger (``op='svd_precut'``, ``discarded`` in squared-sigma
    units).
    """
    width = int(width)
    assert width >= 1, width
    tids = tuple(state.tn.ind_map[bond])
    assert len(tids) == 2, f"bond {bond!r} must join exactly 2 tensors (got {len(tids)})"
    ta, tb = (state.tn.tensor_map[tid] for tid in tids)
    pos_a, pos_b = _pos_of_tensor(ta), _pos_of_tensor(tb)
    r_in = int(state.tn.ind_size(bond))

    QA0, RA, rest_inds_a, rest_dims_a = _qr_split(ta, bond)
    QB0, RB, rest_inds_b, rest_dims_b = _qr_split(tb, bond)
    X0 = RA @ RB.mT
    U, S, Vh = torch.linalg.svd(X0, full_matrices=False)
    s0 = float(S[0]) if S.numel() else 0.0
    re = 1 if s0 <= 0.0 else max(1, int((S > NUMERICAL_ZERO * s0).sum()))
    s_sq = (S * S).to(RDTYPE)
    tot = float(s_sq.sum())
    D_kept = min(width, re)
    sqrt_s = torch.sqrt(S[:D_kept]).to(CDTYPE)
    # write-back mirrors ntu_truncate's exact path: T_A' = QA0 U[:,:k] diag(√S),
    # T_B' = QB0 Vh[:k]^T diag(√S); the ORIGINAL bond ind name is kept.
    ta.modify(data=((QA0 @ U[:, :D_kept]) * sqrt_s)
              .reshape(*rest_dims_a, D_kept).contiguous(),
              inds=rest_inds_a + (bond,))
    tb.modify(data=((QB0 @ Vh[:D_kept].mT) * sqrt_s)
              .reshape(*rest_dims_b, D_kept).contiguous(),
              inds=rest_inds_b + (bond,))
    entry = {
        "op": "svd_precut",
        "bond": str(bond),
        "sites": (int(pos_a), int(pos_b)),
        "dim_in": r_in,
        "dim_out": int(D_kept),
        "width": width,
        "exact_rank": int(re),
        "discarded": float(s_sq[D_kept:].sum()) / tot if tot > 0.0 else 0.0,
    }
    state.ledger.append(entry)
    return entry


def ntu_truncate(state, bond: str, D_cap: int) -> dict:
    """NTU-truncate one bond to ``D_cap`` (contract §3 row): the rung-0 metric
    seed (structured cluster environment, rows = BRA insertion, F6) + the
    alternating pinv optimization loop; per-bond truncation target = ``D_cap``.
    CAP_BINDING at per-bond truncations is NORMAL operation — LOGGED, never
    flagged. Appends the ledger entry to ``state.ledger`` and returns it.

    Procedure: QR-isometrize both bond tensors (``T = Q . R``); the pair
    insertion ``X0 = R_A R_B^T`` is EXACT-rank-compressed first (SVD, dropping
    only ``sigma <= 1e-12 sigma_1`` components — the same drop convention as
    the stab-channel TT; a zero-weight gauge compression, not a truncation)
    which rotates the insertion space to ``diag(S[:re])`` and bounds the metric
    dimension by the exact local rank ``re``. If ``re <= D_cap`` the write-back
    is exact and the metric/pinv machinery is skipped. Otherwise the NTU metric
    ``g`` is assembled on the insertion space (:func:`_cluster_metric`) and
    ``X ~ M_A M_B^T`` (``M`` of width ``D_cap``) is optimized by the seed's
    alternating pinv updates (both sides), starting from the truncated-SVD
    initialization.

    PRE-COMPRESSION (contract v4.2): the dense metric is ``(re^2 x re^2)`` and
    OOMs unguarded at ``re`` in the hundreds — the designed-normal regime. When
    ``re > 4 * D_cap``, the insertion is SVD-pre-truncated to
    ``re_w = 4 * D_cap`` BEFORE the metric is built (4x headroom above D_cap
    preserved for the NTU refinement; the metric is thereby
    <= (4 D_cap)^4 * 16 B ~ 268 MB at D_cap = 16); the pre-cut's discarded
    weight (squared-sigma scale) is logged SEPARATELY as ``precut_discarded``
    (0.0 when no precut). Class (c) design rule with (a) ledger. The exact
    write-back path (``re <= D_cap``) is unchanged.

    Ledger UNITS (contract §2): ``discarded`` is the squared-sigma tail
    ``sum_{k > D_kept} sigma_k^2 / sum sigma^2`` of the local insertion
    spectrum; ``precut_discarded`` is the squared-sigma tail beyond ``re_w``
    dropped by the v4.2 pre-compression (0.0 when no precut); ``ntu_eps`` is
    the F6 quadratic form (a squared norm); ``gap_*`` fields are the pinned
    :func:`gap_rank` read of the same spectrum (ledger effective-rank
    reporting — the only per-bond use of the gap rule).
    """
    D_cap = int(D_cap)
    assert D_cap >= 1, D_cap
    tids = tuple(state.tn.ind_map[bond])
    assert len(tids) == 2, f"bond {bond!r} must join exactly 2 tensors (got {len(tids)})"
    ta, tb = (state.tn.tensor_map[tid] for tid in tids)
    pos_a, pos_b = _pos_of_tensor(ta), _pos_of_tensor(tb)
    r_in = int(state.tn.ind_size(bond))

    QA0, RA, rest_inds_a, rest_dims_a = _qr_split(ta, bond)
    QB0, RB, rest_inds_b, rest_dims_b = _qr_split(tb, bond)
    X0 = RA @ RB.mT                                   # (q_a0, q_b0) pair insertion
    U, S, Vh = torch.linalg.svd(X0, full_matrices=False)
    s0 = float(S[0]) if S.numel() else 0.0
    if s0 <= 0.0:
        re = 1
    else:
        re = max(1, int((S > NUMERICAL_ZERO * s0).sum()))
    s_sq = (S * S).to(RDTYPE)
    tot = float(s_sq.sum())
    re_exact = re
    precut_discarded = 0.0
    if re > 4 * D_cap:
        # v4.2 PRE-COMPRESSION: SVD-pre-truncate the insertion to re_w = 4*D_cap
        # BEFORE building the (re^2 x re^2) metric (see docstring); the pre-cut's
        # discarded weight is logged SEPARATELY (squared-sigma scale).
        re = 4 * D_cap
        precut_discarded = float(s_sq[re:].sum()) / tot if tot > 0.0 else 0.0
    QA = QA0 @ U[:, :re]                              # isometric (U isometric)
    QB = QB0 @ Vh[:re].mT                             # isometric (Vh rows orthonormal)

    D_kept = min(D_cap, re)
    sqrt_s = torch.sqrt(S[:D_kept]).to(CDTYPE)
    MA = torch.zeros((re, D_kept), dtype=CDTYPE, device=X0.device)
    MB = torch.zeros((re, D_kept), dtype=CDTYPE, device=X0.device)
    MA[:D_kept, :] = torch.diag(sqrt_s)
    MB[:D_kept, :] = torch.diag(sqrt_s)               # truncated-SVD init (env-free optimum)

    ntu_eps = 0.0
    ntu_eps_rel = 0.0
    n_sweeps = 0
    env_stats = {"env_gauge_cuts": 0, "env_gauge_discarded_max": 0.0}
    if re > D_cap:
        Rm = torch.diag(S[:re]).to(CDTYPE)
        g, env_stats = _cluster_metric(state, state.layout, pos_a, pos_b, bond, QA, QB,
                                       rest_inds_a, rest_dims_a, rest_inds_b,
                                       rest_dims_b, D_cap)
        g4 = g.reshape(re, re, re, re)  # axes [I, J, i, j]: (bra-A, bra-B, ket-A, ket-B)
        rvec = Rm.reshape(-1)
        r_norm = float((rvec.conj() @ (g @ rvec)).real)

        def eps_of(ma, mb):
            wv = (ma @ mb.mT).reshape(-1) - rvec
            return float((wv.conj() @ (g @ wv)).real)

        # Alternating pinv updates — the seed's C5 step, VERBATIM formulas, on
        # both sides. The seed labels g4's axes "ijIJ" with i,j = its axes 0,1
        # and I,J = axes 2,3; rows are the BRA insertion, so seed-i = bra-A,
        # seed-j = bra-B, seed-I = ket-A, seed-J = ket-B (mapping pinned here).
        eps_prev = eps_of(MA, MB)
        for _ in range(_NTU_MAX_SWEEPS):
            n_sweeps += 1
            GA = torch.einsum("ijIJ,jb,Jd->ibId", g4, MB.conj(), MB).reshape(re * D_kept, re * D_kept)
            JA = torch.einsum("ijIJ,jb,IJ->ib", g4, MB.conj(), Rm).reshape(re * D_kept)
            MA = (torch.linalg.pinv(GA, rtol=_NTU_PINV_RTOL) @ JA).reshape(re, D_kept)
            GB = torch.einsum("ijIJ,ia,Ic->jaJc", g4, MA.conj(), MA).reshape(re * D_kept, re * D_kept)
            JB = torch.einsum("ijIJ,ia,IJ->ja", g4, MA.conj(), Rm).reshape(re * D_kept)
            MB = (torch.linalg.pinv(GB, rtol=_NTU_PINV_RTOL) @ JB).reshape(re, D_kept)
            eps_now = eps_of(MA, MB)
            if eps_prev - eps_now <= _NTU_REL_STOP * max(abs(eps_prev), NUMERICAL_ZERO):
                eps_prev = eps_now
                break
            eps_prev = eps_now
        ntu_eps = eps_prev
        ntu_eps_rel = ntu_eps / max(r_norm, NUMERICAL_ZERO)

    # write-back: T_A' = QA . MA, T_B' = QB . MB — the ORIGINAL bond ind name
    # is kept so the network stays consistent; tags untouched (t.modify).
    ta.modify(data=(QA @ MA).reshape(*rest_dims_a, D_kept).contiguous(),
              inds=rest_inds_a + (bond,))
    tb.modify(data=(QB @ MB).reshape(*rest_dims_b, D_kept).contiguous(),
              inds=rest_inds_b + (bond,))

    discarded = float(s_sq[D_kept:].sum()) / tot if tot > 0.0 else 0.0
    eff_rank, win_ratio, cap_binding = gap_rank(S, D_cap)
    entry = {
        "op": "ntu_truncate",
        "bond": str(bond),
        "sites": (int(pos_a), int(pos_b)),
        "dim_in": r_in,
        "dim_out": int(D_kept),
        "D_cap": D_cap,
        "exact_rank": int(re_exact),
        "discarded": discarded,          # squared-sigma scale (contract units table)
        "precut_discarded": float(precut_discarded),  # v4.2 pre-compression tail (0.0 = no precut)
        "ntu_eps": float(ntu_eps),       # F6 quadratic form (squared norm)
        "ntu_eps_rel": float(ntu_eps_rel),
        "ntu_sweeps": int(n_sweeps),
        "gap_rank": int(eff_rank),
        "gap_ratio": float(win_ratio) if win_ratio != math.inf else float("inf"),
        "cap_binding": bool(cap_binding),  # NORMAL at per-bond truncations — logged only
        # v4.3 metric-side env bounding (copy-only; squared-sigma scale)
        "env_gauge_cuts": int(env_stats["env_gauge_cuts"]),
        "env_gauge_discarded_max": float(env_stats["env_gauge_discarded_max"]),
    }
    state.ledger.append(entry)
    return entry


# --------------------------------------------------------------------------- #
# Non-selective round (F3 loop)                                                #
# --------------------------------------------------------------------------- #
def nonselective_round(state, stabs: list, b: float, arm: str, D_cap: int) -> None:
    """One non-selective measurement round (F3): per stabilizer, the branch sum
    ``rho -> sqrt(E_0) rho sqrt(E_0) + sqrt(E_1) rho sqrt(E_1)``, then per-bond
    NTU truncation; stabilizers processed IN THE GIVEN ORDER, which MUST be
    ``sched.stabilizers`` (the R-gate reference loop order — caller contract).

    Branch-sum realization (identity, documented): both outcome channels are
    DIAGONAL in the same (H-rotated) basis, applied elementwise —
    ``rho[i,j] -> (sqrt(e^0_i) sqrt(e^0_j) + sqrt(e^1_i) sqrt(e^1_j)) rho[i,j]``
    — so the branch sum IS the single diagonal superoperator ``D_0 + D_1``,
    TT-decomposed once and applied once (the same H sandwich serves both
    branches). The summed diagonal ``D_0 + D_1`` is ALSO a function of the
    parity products only (v4.2, refuter-proven), so the summed TT obeys the
    SAME per-bond bound ``(2 min(w_L, w_R) + 1)^2`` as each single branch —
    asserted at that tight bound, NOT 2x subadditivity; the contract's
    EQUALITY pin still applies to the per-outcome :func:`stab_channel_tt`
    only.

    Bond/byte budget (v4.2, byte-denominated): the peak grown 4-neighbor site
    tensor is ``9 * (9 D) * (25 D) * D^2`` complex128 ~ 2.0 GiB at D = 16,
    with x3-4 live copies during insert/QR/metric ~ 6-10 GiB transient —
    inside the 32-GiB card.
    """
    dev = torch.device(state.device)
    layout = state.layout
    for paulis in stabs:
        path = tuple(int(s) for s in layout.plaquette_path(paulis))
        assert len(path) == len(paulis) >= 2, (path, paulis)
        _assert_path_adjacent(layout, path)
        w = len(path)
        d_sum = (_fused_stab_diag(path, 0, b, arm, dev)
                 + _fused_stab_diag(path, 1, b, arm, dev))
        cores, ranks = _tt_svd(d_sum)
        bounds = _tt_rank_bounds(w)
        assert all(r <= bd for r, bd in zip(ranks, bounds)), (
            f"summed stab TT rank above the branch bound: {ranks} vs {bounds} "
            f"(v4.2: D_0 + D_1 is a function of the parity products only, so the "
            f"summed TT obeys the SAME (2 min(w_L,w_R)+1)^2 bound as each branch)")
        x_sites = tuple(sorted(int(s) for s, pp in paulis.items()
                               if str(pp).upper() == "X"))
        tt = StabTT(path=path, cores=cores, x_sites=x_sites, outcome=-1,
                    b=float(b), arm=str(arm).upper(), ranks=ranks)
        # contract §3 stab_channel_tt row: measured ranks LOGGED (re-review
        # 2026-07-10 — both callers previously asserted but never persisted them)
        state.ledger.append({
            "op": "stab_tt_ranks",
            "path": tuple(int(p) for p in path),
            "outcome": -1,  # nonselective summed TT (D_0 + D_1)
            "ranks": tuple(int(r) for r in ranks),
        })
        apply_stab_branch(state, tt)
        # truncate the grown support-path bonds, in path order — v4.3 TWO-PASS
        # (2026-07-10): pass 1 bounds every grown path bond to 4*D_cap by a local
        # SVD gauge cut so the NTU metric cluster (pass 2) never doubles a raw
        # 25*D neighbor bond (byte-infeasible at D=16; see svd_precut_bond).
        pair_bonds = [(_bond_between(state, pa, pb))
                      for pa, pb in zip(path, path[1:])]
        for bname in pair_bonds:
            if bname is not None and int(state.tn.ind_size(bname)) > 4 * int(D_cap):
                svd_precut_bond(state, bname, 4 * int(D_cap))
        for bname in pair_bonds:
            if bname is not None and int(state.tn.ind_size(bname)) > int(D_cap):
                ntu_truncate(state, bname, int(D_cap))


def _bond_between(state, pos_a: int, pos_b: int):
    """The unique bond ind shared by sites ``pos_a`` / ``pos_b`` (post
    ``fuse_multibonds``), or ``None`` if the edge carries no bond."""
    ta = _site_tensor(state, pos_a)
    tb = _site_tensor(state, pos_b)
    shared = tuple(i for i in ta.inds if i in set(tb.inds))
    if not shared:
        return None
    assert len(shared) == 1, (
        f"multibond between Q{pos_a} and Q{pos_b} not fused: {shared}")
    return shared[0]

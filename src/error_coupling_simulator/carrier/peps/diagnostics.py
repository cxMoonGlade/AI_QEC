from __future__ import annotations

r"""Bond-profile, loop-correlation, and loop-rank diagnostics for the single-wire PEPS.

``eps_l`` follows the declared Rudolph-Tindall loop-correlation convention; the
current exact locator remains pending the clean literature reset.

For independence, the ``eps_l`` belief-propagation +
loop-transfer-matrix computation here shares NO code with any reference — the
current known-answer tests recompute the loop spectrum by an independent dense
eigendecomposition written from scratch in the test file and match to 1e-10.
This module is deliberately hand-rolled on explicit ``torch`` tensors (extracted
straight off the quimb ``TensorNetwork`` index maps — no quimb contraction of the
loop) so that independence is real.

The instruments read the state; they never mutate it and consume no host uniforms.
``eps_l`` accepts either a :class:`~.state.PepsState` (production)
or a bare quimb ``TensorNetwork`` carrying a ``.layout`` duck (the synthetic
known-answer networks) — it reads ``tn.layout`` when ``state.layout`` is
absent.
"""

import torch

from ...numerics import NUMERICAL_ZERO
from .state import CDTYPE, QUTRIT, fused_bond_name, phys_name

#: ``eps_l`` bound/roundoff tolerances for the self-check ``eps_l in
#: [0, 1 - 1/D_e^2]`` on the CUT EDGE's own bond dim).
_EPS_L_BOUND_TOL = 1e-9
_LETTERS = "abcdefghijklmnopqrstuvwxyz"


# --------------------------------------------------------------------------- #
# State / layout extraction (PepsState or bare-tn-with-.layout)               #
# --------------------------------------------------------------------------- #
def _tn_layout(state):
    """The (tn, layout) pair from a :class:`PepsState` or a bare TN carrying a
    ``.layout`` duck used by synthetic known-answer networks."""
    tn = getattr(state, "tn", state)
    layout = getattr(state, "layout", None)
    if layout is None:
        layout = getattr(tn, "layout", None)
    if layout is None:
        raise ValueError(
            "diagnostics need a grid layout (state.layout or tn.layout) — the "
            "PepoLayout surface d / grid / pos_at / neighbors / grid_edges")
    return tn, layout


def _site_by_phys(tn, pos: int):
    """The single-wire ket site tensor carrying physical index ``k{pos}``
    (tag-independent — robust to the synthetic known-answer tns which may not
    carry ``Q{pos}`` tags)."""
    ind = phys_name(int(pos))
    if ind not in tn.ind_map:
        raise KeyError(f"physical index {ind!r} absent from the tn (pos {pos})")
    tids = list(tn.ind_map[ind])
    if len(tids) != 1:
        raise RuntimeError(
            f"physical index {ind!r} is shared by {len(tids)} tensors "
            f"(expected 1 — this is the single-wire KET network)")
    return tn.tensor_map[tids[0]]


def _extract_sites(tn, layout) -> dict:
    """Per-site ``{data, inds, phys, bond_ind}`` — ``bond_ind`` maps each
    grid-adjacent neighbor to the SHARED ket bond index name present on the
    tensor (a missing/absent grid edge is simply not listed — dim-1, inert)."""
    n = int(layout.n_data)
    sites = {}
    for pos in range(n):
        t = _site_by_phys(tn, pos)
        inds = list(t.inds)
        bond_ind = {}
        for q in layout.neighbors(pos):
            bn = fused_bond_name(int(pos), int(q))
            if bn in inds:
                bond_ind[int(q)] = bn
        sites[int(pos)] = {"data": t.data, "inds": inds,
                           "phys": phys_name(int(pos)), "bond_ind": bond_ind}
    return sites


# --------------------------------------------------------------------------- #
# Bond-profile instrument                                                     #
# --------------------------------------------------------------------------- #
def bond_profile(state) -> dict:
    """The grid bond profile ``{(p, q): dim}`` (``p < q``) over all grid edges.
    Untouched structurally empty edges read dimension 1."""
    tn, layout = _tn_layout(state)
    prof = {}
    for p, q in layout.grid_edges():
        bn = fused_bond_name(int(p), int(q))
        dim = int(tn.ind_size(bn)) if bn in tn.ind_map else 1
        prof[(int(p), int(q))] = dim
    return prof


def max_bond(state) -> int:
    """Maximum current bond dimension over all grid edges."""
    prof = bond_profile(state)
    return int(max(prof.values())) if prof else 1


# --------------------------------------------------------------------------- #
# ``eps_l`` Rudolph-Tindall loop-correlation BP error                         #
# --------------------------------------------------------------------------- #
def _fresh_letters():
    return iter(_LETTERS)


def _site_reduced(site: dict, msgs_in: dict, open_bonds: tuple) -> torch.Tensor:
    """Contract the grouped NORM-network node ``T_v = ket ⊗ conj(ket)`` (physical
    legs traced) with the incoming BP messages on every bond in ``msgs_in``,
    leaving the bonds in ``open_bonds`` OPEN as (ket, bra) index pairs.

    ``msgs_in``: ``{bond_ind: (D, D) matrix}`` over (ket, bra) of that bond.
    Returns the raw tensor with axes ordered ``(ket_o0, bra_o0, ket_o1, ...)``
    for the open bonds in ``open_bonds`` order. This is the single BP/loop
    contraction primitive (both the message update — one open bond — and the
    loop reduced matrix — two open bonds — call it)."""
    data = site["data"]
    inds = site["inds"]
    pind = site["phys"]
    lets = _fresh_letters()
    pl = next(lets)
    ket_sub, bra_sub = [], []
    bl_map = {}
    for nm in inds:
        if nm == pind:
            ket_sub.append(pl)
            bra_sub.append(pl)
        else:
            kl, bl = next(lets), next(lets)
            bl_map[nm] = (kl, bl)
            ket_sub.append(kl)
            bra_sub.append(bl)
    subs = ["".join(ket_sub), "".join(bra_sub)]
    tensors = [data, data.conj()]
    for bn, mat in msgs_in.items():
        if bn not in bl_map:
            raise KeyError(f"message bond {bn!r} not an index of the site tensor")
        kl, bl = bl_map[bn]
        subs.append(kl + bl)
        tensors.append(mat)
    out_sub = ""
    for bn in open_bonds:
        if bn not in bl_map:
            raise KeyError(f"open bond {bn!r} not an index of the site tensor")
        kl, bl = bl_map[bn]
        out_sub += kl + bl
    eq = ",".join(subs) + "->" + out_sub
    return torch.einsum(eq, *tensors)


def _directed_edges(sites: dict) -> list:
    """All directed edges ``(v, w)`` over materialized grid bonds (both
    orientations)."""
    undirected = set()
    for v, s in sites.items():
        for q in s["bond_ind"]:
            undirected.add((min(v, q), max(v, q)))
    out = []
    for p, q in sorted(undirected):
        out.append((p, q))
        out.append((q, p))
    return out


def _bp_fixed_point(sites: dict, tn, tol: float, max_sweeps: int) -> tuple:
    """Belief-propagation message fixed point on the norm network: one
    matrix message per directed edge over its (ket, bra) bond pair, updated
    ``m_{v->w} = (T_v contracted with all incoming m_{u->v}, u != w, leaving
    (v,w) open)`` and NORMALIZED to unit Frobenius norm each sweep. Returns
    ``(messages, converged, sweeps, max_delta)``; non-convergence is FLAGGED
    (returned), never silently dropped."""
    directed = _directed_edges(sites)
    dev = None
    msg = {}
    for v, w in directed:
        bn = fused_bond_name(v, w)
        D = int(tn.ind_size(bn))
        if dev is None:
            dev = sites[v]["data"].device
        m0 = torch.eye(D, dtype=CDTYPE, device=sites[v]["data"].device)
        nrm = float(torch.linalg.norm(m0))
        msg[(v, w)] = m0 / nrm if nrm > 0.0 else m0
    converged = False
    sweeps = 0
    max_delta = 0.0
    for sweeps in range(1, int(max_sweeps) + 1):
        new = {}
        max_delta = 0.0
        for v, w in directed:
            bond_vw = fused_bond_name(v, w)
            msgs_in = {sites[v]["bond_ind"][q]: msg[(q, v)]
                       for q in sites[v]["bond_ind"] if q != w}
            m = _site_reduced(sites[v], msgs_in, (bond_vw,))
            nrm = torch.linalg.norm(m)
            m = m / nrm.to(m.dtype) if float(nrm) > 0.0 else m
            new[(v, w)] = m
            delta = float(torch.linalg.norm(m - msg[(v, w)]))
            if delta > max_delta:
                max_delta = delta
        msg = new
        if max_delta < float(tol):
            converged = True
            break
    return msg, converged, sweeps, max_delta


def _loop_eps(P: torch.Tensor) -> float:
    """``eps_l = 1 - |lambda_1| / sum_i |lambda_i|`` of a loop transfer matrix
    ``P`` (Rudolph-Tindall Eq. 4). A rank-1 (loop-free) ``P`` gives 0."""
    if not torch.isfinite(P).all():
        return float("nan")
    lam = torch.linalg.eigvals(P)
    mags = lam.abs()
    tot = float(mags.sum())
    if not tot > NUMERICAL_ZERO:
        return 0.0
    return float(1.0 - float(mags.max()) / tot)


def _primitive_loops(layout) -> list:
    """The ``(d-1)^2`` elementary four-site grid squares, each a
    cyclic ``[v0, v1, v2, v3]`` around a unit cell of the ``{0..d-1}^2`` grid."""
    d = int(layout.d)
    loops = []
    for u in range(d - 1):
        for c in range(d - 1):
            loops.append([
                layout.pos_at[(u, c)],
                layout.pos_at[(u, c + 1)],
                layout.pos_at[(u + 1, c + 1)],
                layout.pos_at[(u + 1, c)],
            ])
    return loops


def eps_l(state, *, bp_tol: float = 1e-10, bp_max_sweeps: int = 500) -> dict:
    """The per-loop Rudolph-Tindall BP error ``eps_l`` on the current state's
    norm network.

    Conventions (ours where 2507.11424 is silent — declared class (c)): grouped
    ``(T, T*)`` nodes; primitive loops = the ``(d-1)^2`` unit squares; BP
    messages both directions, unit-Frobenius-normalized, converged to
    ``bp_tol`` (<= ``bp_max_sweeps`` sweeps; non-convergence flagged);
    per loop the transfer matrix is formed for EVERY cut edge (insert the
    converged boundary messages on the non-loop edges, cut one loop edge open,
    full ``eigvals``) and the per-loop value is the MAX over its 4 cuts
    (conservative) with the mean also reported.

    Returns a dict: ``per_loop`` (one entry per loop: corners, ``eps_max``,
    ``eps_mean``, ``eps_cuts``, ``cut_dims``), the run-level ``mean`` (mean over
    loops of ``eps_max``) and ``max``, ``n_loops``, and the BP diagnostics
    (``bp_converged`` / ``bp_sweeps`` / ``bp_max_delta``) + ``bound_violations``
    (cuts landing outside ``[0, 1 - 1/D_e^2]`` beyond roundoff — a
    non-convergence/numerical flag, never raised)."""
    tn, layout = _tn_layout(state)
    d = int(layout.d)
    if d < 2:
        return {"per_loop": [], "mean": 0.0, "max": 0.0, "n_loops": 0,
                "bp_converged": True, "bp_sweeps": 0, "bp_max_delta": 0.0,
                "bound_violations": 0}

    sites = _extract_sites(tn, layout)
    msg, converged, sweeps, max_delta = _bp_fixed_point(
        sites, tn, float(bp_tol), int(bp_max_sweeps))

    per_loop = []
    loop_maxes = []
    bound_violations = 0
    for loop in _primitive_loops(layout):
        # loop edge bonds e[i] between v_i and v_{i+1}
        e_bond = [fused_bond_name(loop[i], loop[(i + 1) % 4]) for i in range(4)]
        e_dim = [int(tn.ind_size(bn)) for bn in e_bond]
        # reduced matrix per loop site: prev = e[(i-1)%4], next = e[i]
        red = []
        for i in range(4):
            v = loop[i]
            prev_b = e_bond[(i - 1) % 4]
            next_b = e_bond[i]
            loop_nbrs = {loop[(i - 1) % 4], loop[(i + 1) % 4]}
            msgs_in = {sites[v]["bond_ind"][q]: msg[(q, v)]
                       for q in sites[v]["bond_ind"] if q not in loop_nbrs}
            raw = _site_reduced(sites[v], msgs_in, (prev_b, next_b))
            dp, dn = int(raw.shape[0]), int(raw.shape[2])
            red.append(raw.reshape(dp * dp, dn * dn))
        eps_cuts = []
        for c in range(4):
            P = red[(c + 1) % 4]
            for k in (2, 3):
                P = P @ red[(c + k) % 4]
            P = P @ red[c]
            eps = _loop_eps(P)
            eps_cuts.append(eps)
            Dc = e_dim[c]
            if eps == eps:  # not NaN
                upper = 1.0 - 1.0 / float(Dc * Dc)
                if eps < -_EPS_L_BOUND_TOL or eps > upper + _EPS_L_BOUND_TOL:
                    bound_violations += 1
        finite = [x for x in eps_cuts if x == x]
        eps_max = max(finite) if finite else float("nan")
        eps_mean = (sum(finite) / len(finite)) if finite else float("nan")
        per_loop.append({
            "corners": tuple(int(x) for x in loop),
            "eps_max": eps_max,
            "eps_mean": eps_mean,
            "eps_cuts": [float(x) for x in eps_cuts],
            "cut_dims": [int(x) for x in e_dim],
        })
        if eps_max == eps_max:
            loop_maxes.append(eps_max)

    mean = (sum(loop_maxes) / len(loop_maxes)) if loop_maxes else 0.0
    mx = max(loop_maxes) if loop_maxes else 0.0
    return {
        "per_loop": per_loop,
        "mean": float(mean),
        "max": float(mx),
        "n_loops": len(per_loop),
        "bp_converged": bool(converged),
        "bp_sweeps": int(sweeps),
        "bp_max_delta": float(max_delta),
        "bound_violations": int(bound_violations),
    }


# --------------------------------------------------------------------------- #
# Gauge-independent loop-closed bond-rank probe                               #
# --------------------------------------------------------------------------- #
def loop_rank_probe(state, bond: str, *, n_probe: int = 80, seed: int = 0,
                    d_ref: int = 16) -> dict:
    """A loop-closed bond-rank probe adapted to the single-wire dim-3 ket
    network. It cuts ``bond`` open
    into two legs, caps every physical leg with a random dim-3 vector, contracts
    to a ``(D, D)`` matrix, stacks ``n_probe`` draws and reads the numerical
    rank of the stacked map: ``rank < D`` (flat) ⇒ a lossless regauge to that
    rank EXISTS; ``rank == D`` with a flat spectrum ⇒ none does.

    Returns ``{bond, dim, rank, beyond_ref, sigma_top}`` — ``beyond_ref`` = the
    squared-sigma weight beyond rank ``d_ref`` (the loop-closed heaviness the
    parent probe reported); ``sigma_top`` = the leading normalized spectrum.
    A diagnostic only — never a gate."""
    import quimb.tensor as qtn  # lazy: keep the module importable without quimb

    tn, layout = _tn_layout(state)
    n = int(layout.n_data)
    if bond not in tn.ind_map:
        raise KeyError(f"loop_rank_probe: bond {bond!r} not in the tn")
    D = int(tn.ind_size(bond))
    dev = _site_by_phys(tn, 0).data.device
    gen = torch.Generator(device="cpu")
    gen.manual_seed(int(seed))
    bond_v = bond + "_v"

    mats = []
    for _ in range(int(n_probe)):
        work = tn.copy()
        # cut: rename `bond` -> `bond_v` on exactly ONE of its two tensors
        tid = sorted(work.ind_map[bond])[0]
        work.tensor_map[tid].reindex_({bond: bond_v})
        # random dim-3 caps on every physical leg
        caps = []
        for pos in range(n):
            re = torch.randn(QUTRIT, generator=gen, dtype=torch.float64)
            im = torch.randn(QUTRIT, generator=gen, dtype=torch.float64)
            vec = (re + 1j * im).to(CDTYPE).to(dev)
            caps.append(qtn.Tensor(vec, inds=(phys_name(pos),)))
        net = qtn.TensorNetwork(tuple(work) + tuple(caps))
        out = net.contract(output_inds=(bond, bond_v), optimize="auto-hq")
        mats.append(out.data.reshape(D, D))

    stack = torch.stack(mats, dim=2).reshape(D, D * len(mats))
    sv = torch.linalg.svdvals(stack)
    s0 = float(sv[0]) if sv.numel() else 0.0
    rank = int((sv > NUMERICAL_ZERO * s0).sum()) if s0 > 0.0 else 0
    sq = (sv * sv).real
    tot = float(sq.sum())
    beyond = float(sq[int(d_ref):].sum()) / tot if tot > 0.0 and sv.numel() > d_ref else 0.0
    top = (sv / s0).tolist()[:24] if s0 > 0.0 else []
    return {"bond": str(bond), "dim": int(D), "rank": int(rank),
            "beyond_ref": float(beyond), "sigma_top": [float(x) for x in top]}


__all__ = ["bond_profile", "max_bond", "eps_l", "loop_rank_probe"]

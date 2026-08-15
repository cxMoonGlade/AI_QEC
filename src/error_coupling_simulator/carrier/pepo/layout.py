from __future__ import annotations

r"""PEPO layout and codestate builder for a rotated ``d x d`` XZZX patch.

This module owns the diamond-to-integer-grid transform, frozen-cut site lists,
plaquette paths, and codestate construction. Dynamics and truncation are owned by
``dynamics.py``; contraction and terminal reads are owned by ``sampler.py``.

Engine position ``pos`` with
raw diamond coordinate ``(x, y) = sched.data_coords[pos]`` maps to

    ``u' = (x + y)/2 - min,   v' = (x - y)/2 - min``

and ``(u', v')`` is asserted integral, unique, and exactly the ``{0..d-1}^2`` grid.
``u`` indexes the D-P
inter-column direction used by :meth:`PepoLayout.plaquette_path` (a path "column crossing"
= a step changing ``u``); the boundary-MPS contraction axis is the SAMPLER's own
algorithm-internal convention (``sampler.py``: a boundary-MPS "column" = fixed ``v``, the
MPS running over ``u``). The contraction value is axis-independent.

``frozen_cut_a`` / ``frozen_cut_b`` use a deterministic max-balanced x-threshold rule:
scan unique x thresholds, define ``A = {pos: x <= t + 1e-9}``, maximize
``min(|A|, |B|)``, and take the first maximum. At the d3_at_q6_7 patch this yields
``A = (0, 1, 2) | B = (3..8)`` — a STAIRCASE in ``(u', v')``, not a grid column; every frozen
number is defined at THAT site list.

Codestate PEPO construction produces the fused-leg representation of ``|m><m|``:

  1. PURE-STATE seed: the oracle's ``_codestate_vector`` convention — the H^(x)n-SPREAD seed
     ``H^(x)n |0...0>`` as a bond-free product PEPS of per-site qutrit vectors
     ``(1, 1, 0)/sqrt(2)``; a literal ``|0...0>`` seed can be exactly annihilated in the
     ``m = 1`` sector.
  2. Per check ONE bond-2 W-tensor chain (the D-P construction): each projector
     ``(I + c.g)/2`` (``c = +1`` for stabilizers, ``c = (-1)^m`` for the logical-sector
     projector, applied in ``sched.stabilizers`` order then the logical — the oracle's
     order) is the bond-2 MPO ``W_1 = [I/2, c.P_1/2]``, ``W_mid = diag(I, P_j)``,
     ``W_last = [I, P_w]`` contracted along ``layout.plaquette_path(support)`` (grid-adjacent,
     one inter-column crossing where possible); chain legs are FUSED into the single
     per-grid-edge bond. Paulis are the oracle's qutrit embedding (X/Z on the ``{0,1}``
     block, identity on ``|2>``), so the ``|2>`` rows stay exactly zero.
  3. Nonzero-norm assertion for both logical sectors: with ``tr_stab`` the squared norm
     after the stabilizer projectors and ``tr_m`` after the logical-sector projector,
     both sectors ``tr_m`` and ``tr_stab - tr_m`` must exceed ``NUMERICAL_ZERO * tr_stab``
     (scale-relative so the check stays d-generic; annihilation gives ~0).
  4. Site-local ket(x)bra fuse into the FUSED-leg PEPO of ``rho = |m><m|``: per site the
     rank<=5 tensor ``T (x) conj(T)`` with the physical pair fused ROW-MAJOR ket-major into
     ``k{pos}`` of dim 9 (``k = 3*t_ket + t_bra``; every superoperator uses this)
     and each virtual pair fused ket-major into the grid-edge bond ``B{p}_{q}`` (``p < q``).
     Untouched grid edges are materialized as dim-1 bonds so EVERY grid edge carries a bond
     index. Tensors are trace-normalized (``tr_m^(-1/n)`` per site), so
     ``pepo_trace(state) == 1`` and the dense reconstruction equals the oracle's normalized
     ``rho`` (global phase cancels in ``|m><m|``).

Current dense-reference tests require the d3 reconstruction to equal
``QutritDM.init_logical(m)``'s ``rho`` for
``m = 0`` AND ``m = 1``, max-abs <= 1e-12 (``carrier/exact/qutrit_dm.py``; the logical
projector mirrors the oracle's ``self._logical_z or {0: "Z"}`` wiring through
``sv_sampler``'s ``set_code`` — logical_z is set only for a Z-kind logical).

Index/tag conventions shared by the sibling modules:

  * site tensor tag ``Q{pos}`` (ENGINE position, the streams/stab key space);
  * fused physical index ``k{pos}``, dim 9, ``k = 3*t_ket + t_bra`` (row-major vec);
  * fused virtual bond between grid-adjacent positions ``p < q``: ``B{p}_{q}``
    (:func:`fused_bond_name`); present on EVERY grid edge (dim 1 when structurally empty);
  * tensors torch complex128 on the passed-in CUDA device, asserted at
    :class:`PepoState` construction, rank <= 5.

GPU-only, complex128; devices are passed in, never selected implicitly.
"""

import math

import torch

from ...numerics import NUMERICAL_ZERO
from ..exact.qutrit_dm import CDTYPE, qudit_hadamard

#: qutrit local dimension of the carrier (fused physical leg = _QUTRIT**2 = 9).
_QUTRIT = 3
_FUSED_DIM = _QUTRIT * _QUTRIT
#: Coordinate comparison tolerance for the x-threshold scan
#: (``xs[p] <= t + 1e-9``); not a numerical floor (see NUMERICAL_ZERO).
_COORD_TOL = 1e-9


# --------------------------------------------------------------------------- #
# Naming conventions shared with dynamics.py and sampler.py                   #
# --------------------------------------------------------------------------- #
def site_tag(pos: int) -> str:
    """The quimb tag of the site tensor at engine position ``pos``."""
    return f"Q{int(pos)}"


def fused_phys_name(pos: int) -> str:
    """The fused d^2 = 9 physical index name at engine position ``pos``."""
    return f"k{int(pos)}"


def fused_bond_name(p: int, q: int) -> str:
    """The fused virtual bond index name on the grid edge between positions ``p, q``."""
    a, b = (int(p), int(q)) if int(p) < int(q) else (int(q), int(p))
    return f"B{a}_{b}"


def _ket_bond_name(p: int, q: int) -> str:
    """Ket-layer (pure-state) bond name during construction (internal)."""
    a, b = (int(p), int(q)) if int(p) < int(q) else (int(q), int(p))
    return f"e{a}_{b}"


# --------------------------------------------------------------------------- #
# Layout                                                                      #
# --------------------------------------------------------------------------- #
class PepoLayout:
    """Diamond -> integer-grid layout of a rotated d x d XZZX patch.

    Attributes: ``sched`` (the parsed XZZX schedule), ``n_data``,
    ``d``, ``grid`` (``pos -> (u, v)`` with ``u, v in {0..d-1}``), ``pos_at``
    (``(u, v) -> pos``), ``frozen_cut_a`` / ``frozen_cut_b`` (the max-balanced
    x-threshold cut site lists; ``A == (0, 1, 2)`` at the d3_at_q6_7 patch).
    """

    def __init__(self, sched, n_data: int, d: int, grid: dict, pos_at: dict,
                 frozen_cut_a: tuple, frozen_cut_b: tuple) -> None:
        self.sched = sched
        self.n_data = int(n_data)
        self.d = int(d)
        self.grid = dict(grid)
        self.pos_at = dict(pos_at)
        self.frozen_cut_a = tuple(int(p) for p in frozen_cut_a)
        self.frozen_cut_b = tuple(int(p) for p in frozen_cut_b)

    # ------------------------------------------------------------------ #
    @classmethod
    def from_sched(cls, sched) -> "PepoLayout":
        """Build the layout from a parsed XZZX schedule; assert integrality,
        uniqueness, and d x d coverage of the transformed ``(u', v')`` grid."""
        coords = [tuple(float(x) for x in c) for c in sched.data_coords]
        n_data = len(coords)
        if n_data < 1:
            raise ValueError("sched has no data coordinates")
        d = math.isqrt(n_data)
        if d * d != n_data:
            raise ValueError(f"n_data = {n_data} is not a perfect square (need a d x d patch)")

        us_raw = [(c[0] + c[1]) / 2.0 for c in coords]
        vs_raw = [(c[0] - c[1]) / 2.0 for c in coords]
        u_min, v_min = min(us_raw), min(vs_raw)
        grid: dict[int, tuple[int, int]] = {}
        pos_at: dict[tuple[int, int], int] = {}
        for pos in range(n_data):
            uf, vf = us_raw[pos] - u_min, vs_raw[pos] - v_min
            u, v = int(round(uf)), int(round(vf))
            if abs(uf - u) > _COORD_TOL or abs(vf - v) > _COORD_TOL:
                raise ValueError(
                    f"grid transform not integral at pos {pos}: (u', v') = ({uf}, {vf})")
            if not (0 <= u < d and 0 <= v < d):
                raise ValueError(
                    f"grid transform out of the {d}x{d} range at pos {pos}: ({u}, {v})")
            if (u, v) in pos_at:
                raise ValueError(
                    f"grid transform not unique: positions {pos_at[(u, v)]} and {pos} "
                    f"both map to ({u}, {v})")
            grid[pos] = (u, v)
            pos_at[(u, v)] = pos
        # uniqueness + range + count == d*d ==> the full d x d grid is covered.
        if len(pos_at) != n_data:
            raise ValueError("grid transform did not cover the d x d grid")

        cut_a, cut_b = cls._frozen_cut(coords, n_data)
        return cls(sched=sched, n_data=n_data, d=d, grid=grid, pos_at=pos_at,
                   frozen_cut_a=cut_a, frozen_cut_b=cut_b)

    @staticmethod
    def _frozen_cut(coords: list, n_data: int) -> tuple[tuple, tuple]:
        """Return the deterministic max-balanced x-threshold cut.

        Scan unique x thresholds except the largest, set
        ``A = {pos: x <= t + 1e-9}``, score ``min(|A|, |B|)``, and retain the
        first (smallest-threshold) maximum.
        """
        xs = [float(c[0]) for c in coords]
        uniq_x = sorted(set(xs))
        if len(uniq_x) < 2:
            raise ValueError("cannot form an x-threshold bisection (single x value)")
        best = None  # (min(|A|,|B|), threshold, A)
        for t in uniq_x[:-1]:
            a = [p_ for p_ in range(n_data) if xs[p_] <= t + _COORD_TOL]
            score = min(len(a), n_data - len(a))
            if best is None or score > best[0]:
                best = (score, t, a)
        a_sites = tuple(sorted(best[2]))
        b_sites = tuple(sorted(set(range(n_data)) - set(a_sites)))
        return a_sites, b_sites

    # ------------------------------------------------------------------ #
    def neighbors(self, pos: int) -> list[int]:
        """Grid-adjacent engine positions of ``pos`` (|du| + |dv| == 1), sorted."""
        u, v = self.grid[int(pos)]
        out = []
        for du, dv in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = self.pos_at.get((u + du, v + dv))
            if q is not None:
                out.append(q)
        return sorted(out)

    def grid_edges(self) -> list[tuple[int, int]]:
        """All grid edges as position pairs ``(p, q)`` with ``p < q``, sorted."""
        edges = set()
        for p in range(self.n_data):
            for q in self.neighbors(p):
                edges.add((p, q) if p < q else (q, p))
        return sorted(edges)

    def plaquette_path(self, paulis: dict) -> list:
        """Ordered grid-adjacent site path through a stabilizer/logical support.

        Returns a Hamiltonian path over ``paulis``' support in the grid-adjacency graph
        (consecutive sites |du| + |dv| == 1), selected by (i) MINIMAL number of
        inter-column crossings (steps changing ``u`` — "one inter-column crossing where
        possible", the D-P convention; a 2x2 plaquette always admits a 1-crossing path),
        then (ii) the lexicographically smallest position sequence (deterministic
        tie-break; a path and its reverse are both candidates). Raises ``ValueError``
        when the support admits no grid-adjacent path.
        """
        sites = sorted(int(s) for s in paulis)
        if not sites:
            raise ValueError("empty support")
        for s in sites:
            if s not in self.grid:
                raise ValueError(f"support site {s} is not a data position of this layout")
        if len(sites) == 1:
            return [sites[0]]

        coords = {s: self.grid[s] for s in sites}

        def _adjacent(a: int, b: int) -> bool:
            (ua, va), (ub, vb) = coords[a], coords[b]
            return abs(ua - ub) + abs(va - vb) == 1

        best: tuple | None = None  # (n_crossings, path tuple)

        def _dfs(path: list, remaining: set, crossings: int) -> None:
            nonlocal best
            if best is not None and crossings > best[0]:
                return  # crossings only grow along a path — safe prune
            if not remaining:
                key = (crossings, tuple(path))
                if best is None or key < best:
                    best = key
                return
            for nxt in sorted(remaining):
                if _adjacent(path[-1], nxt):
                    du = coords[nxt][0] != coords[path[-1]][0]
                    _dfs(path + [nxt], remaining - {nxt}, crossings + (1 if du else 0))

        for start in sites:
            _dfs([start], set(sites) - {start}, 0)
        if best is None:
            raise ValueError(
                f"support {sites} admits no grid-adjacent Hamiltonian path")
        return list(best[1])


# --------------------------------------------------------------------------- #
# State object                                                                #
# --------------------------------------------------------------------------- #
class PepoState:
    """The fused-leg density-matrix PEPO state.

    Attributes: ``tn`` (quimb ``TensorNetwork``; one rank<=5 site tensor per data
    qutrit, tagged ``Q{pos}``, fused physical index ``k{pos}`` of dim 9 with
    ``k = 3*t_ket + t_bra`` row-major, virtual bonds ``B{p}_{q}`` on the grid edges),
    ``layout`` (:class:`PepoLayout`), ``device`` (str), ``ledger`` (list of dicts —
    the ONLY tracked bond metadata: per-truncation discarded weight (squared-sigma
    scale) + per-round trace shift; appended by ``dynamics.ntu_truncate``).

    Construction asserts torch complex128 tensors on a CUDA
    device, rank <= 5, one tensor per position with the dim-9 fused physical leg.
    Hermiticity of the represented ``rho`` is deliberately NOT asserted per-tensor
    because the fused-leg PEPO does not expose it locally.
    """

    def __init__(self, tn, layout: PepoLayout, device: str, ledger: list | None = None) -> None:
        self.tn = tn
        self.layout = layout
        self.device = str(device)
        self.ledger = [] if ledger is None else ledger

        dev = torch.device(self.device)
        if dev.type != "cuda":
            raise ValueError(
                f"PepoState tensors require a CUDA device; got {self.device!r}")
        sites = _site_tensors_by_pos(tn, layout.n_data)
        for pos in range(layout.n_data):
            t = sites[pos]
            data = t.data
            if not torch.is_tensor(data):
                raise TypeError(f"site {pos}: tensor data is not a torch tensor")
            if data.dtype != CDTYPE:
                raise TypeError(f"site {pos}: dtype {data.dtype} != complex128")
            if data.device.type != dev.type:
                raise ValueError(
                    f"site {pos}: tensor device {data.device} != state device {self.device}")
            if len(t.inds) > 5:
                raise ValueError(f"site {pos}: rank {len(t.inds)} > 5")
            k = fused_phys_name(pos)
            if k not in t.inds:
                raise ValueError(f"site {pos}: fused physical index {k!r} missing")
            if int(data.shape[t.inds.index(k)]) != _FUSED_DIM:
                raise ValueError(f"site {pos}: fused physical index {k!r} is not dim 9")


def _site_tensors_by_pos(tn, n_data: int) -> dict:
    """Map engine position -> its (unique) site tensor via the ``Q{pos}`` tags."""
    out: dict[int, object] = {}
    for t in tn.tensors:
        for tg in t.tags:
            s = str(tg)
            if s.startswith("Q") and s[1:].isdigit():
                pos = int(s[1:])
                if pos in out:
                    raise ValueError(f"duplicate site tensor for tag Q{pos}")
                out[pos] = t
    missing = [pos for pos in range(n_data) if pos not in out]
    if missing:
        raise ValueError(f"missing site tensors for positions {missing}")
    return out


# --------------------------------------------------------------------------- #
# Codestate construction internals (pure-state ket layer, plain torch)        #
# --------------------------------------------------------------------------- #
def _qutrit_pauli(kind: str, device) -> torch.Tensor:
    """``X``/``Z`` on the computational ``{0,1}`` block, identity on ``|2>`` — the
    oracle's ``_single_qudit_pauli`` convention (``carrier/exact/qutrit_dm.py``)."""
    kind = str(kind).upper()
    m = torch.zeros((_QUTRIT, _QUTRIT), dtype=CDTYPE, device=device)
    if kind == "X":
        m[0, 1] = 1.0
        m[1, 0] = 1.0
    elif kind == "Z":
        m[0, 0] = 1.0
        m[1, 1] = -1.0
    else:
        raise ValueError(f"unsupported support Pauli {kind!r} (expected 'X' or 'Z')")
    m[2, 2] = 1.0
    return m


def _fuse_pair(data: torch.Tensor, inds: list, major: str, minor: str) -> tuple:
    """Fuse two named axes into one (``major`` axis MAJOR, row-major combine); the
    fused axis keeps the ``major`` name/slot. Both endpoint tensors of a bond fuse in
    the same (major, minor) order, so the joint index stays consistent."""
    ia, ib = inds.index(major), inds.index(minor)
    order = [ax for ax in range(data.ndim) if ax != ib]
    ja = order.index(ia)
    order.insert(ja + 1, ib)
    data = data.permute(order).contiguous()
    shape = list(data.shape)
    data = data.reshape(shape[:ja] + [shape[ja] * shape[ja + 1]] + shape[ja + 2:])
    new_inds = [nm for nm in inds if nm != minor]
    return data, new_inds


def _apply_chain_operator(ket: dict, layout: PepoLayout, paulis: dict, coeff: float,
                          chain_tag: int, device) -> None:
    """Apply the projector ``(I + coeff * prod_q P_q)/2`` to the ket layer as ONE
    bond-2 W-tensor chain along ``layout.plaquette_path(paulis)`` (D-P construction);
    chain legs are fused into the single per-grid-edge bond. Mutates ``ket`` in place.

    ``ket``: ``pos -> (torch tensor, index-name list)`` with the physical index at
    axis 0 (an invariant every step here preserves).
    """
    path = layout.plaquette_path(paulis)
    w = len(path)
    eye = torch.eye(_QUTRIT, dtype=CDTYPE, device=device)
    ops = {pos: _qutrit_pauli(paulis[pos], device) for pos in path}
    cf = complex(coeff)

    if w == 1:
        pos = path[0]
        data, inds = ket[pos]
        op = 0.5 * (eye + cf * ops[pos])
        ket[pos] = (torch.tensordot(op, data, dims=([1], [0])), inds)
        return

    chain = [f"_c{int(chain_tag)}_{i}" for i in range(w - 1)]
    for i, pos in enumerate(path):
        data, inds = ket[pos]
        pauli = ops[pos]
        if i == 0:
            wt = torch.stack([0.5 * eye, (0.5 * cf) * pauli], dim=-1)   # (pout, pin, cR)
            new_names = [chain[0]]
        elif i == w - 1:
            wt = torch.stack([eye, pauli], dim=-1)                      # (pout, pin, cL)
            new_names = [chain[i - 1]]
        else:
            wt = torch.zeros((_QUTRIT, _QUTRIT, 2, 2), dtype=CDTYPE, device=device)
            wt[:, :, 0, 0] = eye                                        # (pout, pin, cL, cR)
            wt[:, :, 1, 1] = pauli
            new_names = [chain[i - 1], chain[i]]
        out = torch.tensordot(wt, data, dims=([1], [0]))  # (pout, chains..., rest...)
        ket[pos] = (out, [inds[0]] + new_names + inds[1:])

    # fuse each chain leg into the (single) bond of its grid edge
    for i in range(w - 1):
        p, q = path[i], path[i + 1]
        ename = _ket_bond_name(p, q)
        for pos in (p, q):
            data, inds = ket[pos]
            if ename in inds:
                data, inds = _fuse_pair(data, inds, ename, chain[i])
            else:
                inds = [ename if nm == chain[i] else nm for nm in inds]
            ket[pos] = (data, inds)


def _scalar_to_float(val) -> float:
    """Real part of a contraction scalar (backend number, 0-dim torch tensor, or a
    0-dim quimb Tensor — version-dependent return types are all accepted)."""
    if hasattr(val, "data") and not torch.is_tensor(val):  # 0-dim quimb Tensor
        val = val.data
    if torch.is_tensor(val):
        val = val.item()
    return float(complex(val).real)


def _ket_norm_sq(ket: dict, layout: PepoLayout) -> float:
    """``<psi|psi>`` of the ket layer via the single-layer transfer network (per site
    ``sum_p T[p, e...] conj(T)[p, e~...]`` with each ``(e, e~)`` pair fused ket-major),
    contracted exactly with quimb. Equals the trace of the unnormalized fused PEPO."""
    import quimb.tensor as qtn  # lazy: keep the module importable without quimb

    tensors = []
    for pos in range(layout.n_data):
        data, inds = ket[pos]
        t = torch.tensordot(data, data.conj(), dims=([0], [0]))
        tinds = inds[1:] + [nm + "~" for nm in inds[1:]]
        for nm in list(inds[1:]):
            t, tinds = _fuse_pair(t, tinds, nm, nm + "~")
        tensors.append(qtn.Tensor(data=t, inds=tuple(tinds), tags={site_tag(pos)}))
    val = qtn.TensorNetwork(tensors).contract(output_inds=())
    return _scalar_to_float(val)


# --------------------------------------------------------------------------- #
# Public builders                                                             #
# --------------------------------------------------------------------------- #
def build_codestate_pepo(sched, m: int, device: str = "cuda") -> PepoState:
    """Build the codestate ``rho = |m><m|`` as a fused-leg PEPO :class:`PepoState`.

    The construction applies ``prod_g (I + g)/2`` and the logical-sector
    projector to the H^(x)n-spread seed (the independent dense reference's
    ``_codestate_vector``
    convention) as bond-2 W-tensor chains, qutrit-embedded (``|2>`` rows exactly zero),
    then fused site-locally into the PEPO of ``|m><m|`` (see the module docstring for
    the full construction + conventions). Nonzero norm is asserted for BOTH ``m``
    sectors. The result is trace-normalized (``Tr(rho) == 1``).

    The logical projector mirrors the independent dense reference wiring:
    ``sv_sampler``'s
    ``set_code`` passes ``logical_z = sched.logical`` only when ``sched.logical_kind``
    is ``'Z'``; ``QutritDM._codestate_vector`` then uses ``self._logical_z or
    {0: "Z"}``; the same fallback applies here.
    """
    layout = PepoLayout.from_sched(sched)
    dev = torch.device(device)
    mm = int(m)
    if mm not in (0, 1):
        raise ValueError(f"logical index m must be 0 or 1 (got {m})")
    n = layout.n_data

    # 1. H-spread seed: per-site H|0> = (1, 1, 0)/sqrt(2) (zero |2> support).
    had = qudit_hadamard(_QUTRIT, dev)
    seed = had[:, 0].clone().contiguous()
    ket: dict[int, tuple] = {pos: (seed.clone(), [f"p{pos}"]) for pos in range(n)}

    # 2. Stabilizer projectors, in sched.stabilizers order (the oracle's order).
    tag = 0
    for g in sched.stab_paulis():
        _apply_chain_operator(ket, layout, dict(g), 1.0, tag, dev)
        tag += 1
    tr_stab = _ket_norm_sq(ket, layout)
    if not tr_stab > NUMERICAL_ZERO:
        raise RuntimeError(
            f"stabilizer projection collapsed the H-spread seed to zero norm ({tr_stab})")

    # 3. Logical-sector projector (I + (-1)^m Z_L)/2 — oracle wiring (see docstring).
    lkind = str(getattr(sched, "logical_kind", "Z")).upper()
    logical = dict(sched.logical) if (lkind == "Z" and sched.logical) else {0: "Z"}
    _apply_chain_operator(ket, layout, logical, float((-1.0) ** mm), tag, dev)
    tr_m = _ket_norm_sq(ket, layout)
    tr_other = tr_stab - tr_m  # sectors are complementary: P_0 + P_1 = I on the stab space
    floor = NUMERICAL_ZERO * tr_stab
    if not (tr_m > floor and tr_other > floor):
        raise RuntimeError(
            f"codestate sector norm assert failed (both logical sectors must be nonzero): "
            f"m={mm} sector {tr_m:.3e}, other sector {tr_other:.3e}, "
            f"stab-projected mass {tr_stab:.3e}")

    # structural |2>-mass zero on the ket layer (exact by construction; cheap guard).
    for pos in range(n):
        data, _inds = ket[pos]
        if float(data[2].abs().max()) > NUMERICAL_ZERO:
            raise RuntimeError(f"site {pos}: |2> row of the codestate ket is not zero")

    # 4. Site-local ket(x)bra fuse -> fused-leg PEPO tensors; trace-normalize.
    import quimb.tensor as qtn  # lazy: keep the module importable without quimb

    trace_scale = tr_m ** (-1.0 / n)
    tensors = []
    for pos in range(n):
        data, inds = ket[pos]
        pep = torch.tensordot(data, data.conj(), dims=0) * trace_scale
        pinds = list(inds) + [nm + "~" for nm in inds]
        # physical pair -> k{pos} = 3*t_ket + t_bra (ket major, row-major).
        pep, pinds = _fuse_pair(pep, pinds, f"p{pos}", f"p{pos}~")
        pinds = [fused_phys_name(pos) if nm == f"p{pos}" else nm for nm in pinds]
        # each virtual pair -> the fused grid-edge bond B{p}_{q} (ket MAJOR).
        for nm in list(inds[1:]):
            pep, pinds = _fuse_pair(pep, pinds, nm, nm + "~")
        for q in layout.neighbors(pos):
            ename = _ket_bond_name(pos, q)
            bname = fused_bond_name(pos, q)
            if ename in pinds:
                pinds = [bname if x == ename else x for x in pinds]
            elif bname not in pinds:
                pep = pep.unsqueeze(-1)  # materialize the untouched grid edge (dim 1)
                pinds = pinds + [bname]
        tensors.append(qtn.Tensor(data=pep.contiguous(), inds=tuple(pinds),
                                  tags={site_tag(pos)}))

    tn = qtn.TensorNetwork(tensors)
    return PepoState(tn=tn, layout=layout, device=str(device), ledger=[])


def dense_rho(state: PepoState) -> torch.Tensor:
    """Dense ``(3^n, 3^n)`` reconstruction of the PEPO for bounded comparisons.

    Asserts ``n_data <= 9`` (the qutrit-DM ceiling; a d5 patch has no dense bridge).
    Row/column index convention matches the independent dense reference: engine
    position 0 is the MOST-significant qutrit factor.
    """
    import quimb.tensor as qtn  # lazy: keep the module importable without quimb

    layout = state.layout
    n = layout.n_data
    assert n <= 9, f"dense_rho supports the d3 bounded reference only (n_data = {n} > 9)"

    sites = _site_tensors_by_pos(state.tn, n)
    tensors = []
    for pos in range(n):
        t = sites[pos]
        data = t.data
        inds = list(t.inds)
        ax = inds.index(fused_phys_name(pos))
        shape = list(data.shape)
        if shape[ax] != _FUSED_DIM:
            raise ValueError(f"site {pos}: fused physical leg is not dim 9")
        # unfuse k = 3*t_ket + t_bra -> (t_ket, t_bra), ket MAJOR (row-major inverse).
        new_shape = shape[:ax] + [_QUTRIT, _QUTRIT] + shape[ax + 1:]
        new_inds = inds[:ax] + [f"pk{pos}", f"pb{pos}"] + inds[ax + 1:]
        tensors.append(qtn.Tensor(data=data.reshape(new_shape), inds=tuple(new_inds)))

    out_inds = tuple([f"pk{p}" for p in range(n)] + [f"pb{p}" for p in range(n)])
    res = qtn.TensorNetwork(tensors).contract(output_inds=out_inds)
    dim = _QUTRIT ** n
    return res.data.reshape(dim, dim)

from __future__ import annotations

r"""Double-layer ``<psi| Pi |psi>`` boundary-MPS contraction for the single-wire
PEPS (RUNG-B spike).

Binding doc: ``docs/nonpauli_teacher/peps_singlewire_spike_contract.md`` §2 (rows
``born_read_stab`` / ``terminal_readout``), §3 (row "double-layer caps"), §6.2
(the per-read accuracy instruments), grounded on SF9: the parent boundary-MPS
skeleton (column sweep / absorb / one-site variational fit / reverse-pass cache)
is layer-count-agnostic — ONLY the per-column tensor construction encoded the
doubled-wire ``Tr(rho * Pi)`` semantics, and that construction is what this
module replaces with the ket + conj-bra DOUBLE layer.

Two-layer columns are kept as ket/bra TENSOR PAIRS (one ket + one conj-bra
tensor per row, sharing the dim-3 physical index; bra bond inds renamed
``nm -> nm~``): materializing a per-site doubled tensor would cost
``prod_bonds D^2`` bytes (D^8 on an interior site — byte-infeasible at the WP1
scale), while the one-site variational fit contracts the pair lazily against the
bounded boundary MPS. The reused pieces (``_max_row_bond`` row-bond product,
``ROW{u}`` tags, the fit-call pattern) are imported from the parent sampler; the
fit initial guess is SEEDED here (SW-S7: the parent's unseeded ``torch.randn``
is a declared nondeterminism source — the spike seeds it per read so gate runs
are replayable).

Two-term stab read (SF9, transfers verbatim as an operator identity):

    ``<E_s> = 1/2 <psi|psi> + 1/2 (-1)^s <psi| (x)_q M_q |psi>``  (N and M)

with the RT1 corollary that q0 + q1 == N IDENTICALLY (both derive from the same
two contractions) — a q0+q1 "closure" is structurally vacuous and is NOT an
instrument here; the genuine per-read accuracy instruments are §6.2's
(:func:`cross_route_q1` — the branch-norm route through a DIFFERENT network —
and :func:`chib_doubling_delta`).

GPU-only, complex128 (SW-S8); referee-independent (local gate formulas, D4).
"""

import torch
import quimb.tensor as qtn

from ...numerics import NUMERICAL_ZERO
from ..pepo.sampler import _FIT_MAX_ITERATIONS, _FIT_TOL, _max_row_bond, _row_tag, _to_complex
from .stab_tt import SingleWireStabTT, apply_stab_branch, leaked_weight, stab_tt_singlewire
from .state import CDTYPE, QUTRIT, PepsState, phys_name, qutrit_gate, site_tensor

#: Open-index names of the 1-site RDM read (:func:`site_rdm`): ket / bra slot.
RDM_KET_IND = "_rdmK"
RDM_BRA_IND = "_rdmB"


# --------------------------------------------------------------------------- #
# Double-layer column construction (the SF9 replacement piece)                 #
# --------------------------------------------------------------------------- #
def _bra_ind(nm: str) -> str:
    """The bra-layer name of a ket bond ind (global deterministic rename)."""
    return nm + "~"


def _site_pair(state: PepsState, pos: int, op, row_tag: str, open_phys: bool):
    """The (ket, bra) tensor pair of one site for the double-layer network.

    ket = ``op |psi>``'s site tensor (op contracted on the dim-3 physical leg;
    ``op is None`` = identity); bra = ``conj(T)`` with every BOND ind renamed
    ``nm -> nm~`` (the physical ind stays shared, so the pair closes the site
    unless ``open_phys``, in which case ket/bra physical inds become the RDM
    open pair). Both tensors carry ONLY ``row_tag`` (throwaway network — no
    ``Q{pos}`` tags, so site lookups never alias into read networks).
    """
    t = site_tensor(state, pos)
    data = t.data
    inds = list(t.inds)
    k = phys_name(pos)
    ax = inds.index(k)
    if op is None:
        kdata = data
    else:
        opt = torch.as_tensor(op, dtype=CDTYPE, device=data.device)
        if opt.shape != (QUTRIT, QUTRIT):
            raise ValueError(f"cap op at pos {pos} must be (3, 3), got {tuple(opt.shape)}")
        kdata = torch.movedim(torch.tensordot(opt, data, dims=([1], [ax])), 0, ax)
    kinds = list(inds)
    binds = [nm if nm == k else _bra_ind(nm) for nm in inds]
    if open_phys:
        kinds[ax] = RDM_KET_IND
        binds[ax] = RDM_BRA_IND
    ket = qtn.Tensor(kdata, inds=tuple(kinds), tags={row_tag})
    bra = qtn.Tensor(data.conj(), inds=tuple(binds), tags={row_tag})
    return ket, bra


def _double_column_tn(state: PepsState, c: int, ops: dict,
                      open_pos: int | None = None) -> "qtn.TensorNetwork":
    """Column ``c`` (sites with grid ``v == c``) of the double-layer network:
    per row ``u`` the (ket, bra) pair tagged ``ROW{u}`` (the parent column
    convention — v = c columns, ROW{u} tags — contract §3 row)."""
    layout = state.layout
    d = int(layout.d)
    tensors = []
    for u in range(d):
        pos = layout.pos_at[(u, c)]
        ket, bra = _site_pair(state, pos, ops.get(pos), _row_tag(u),
                              open_phys=(open_pos is not None and int(open_pos) == pos))
        tensors.extend((ket, bra))
    return qtn.TensorNetwork(tensors)


def _merge(tn_a, tn_b) -> "qtn.TensorNetwork":
    """Union of two row-tagged TNs WITHOUT contracting the row groups (the
    double-layer absorb: the parent's per-row pre-contraction would materialize
    the doubled tensors — see the module docstring; the fit contracts lazily)."""
    if tn_a is None:
        return tn_b
    if tn_b is None:
        return tn_a
    return qtn.TensorNetwork(tuple(tn_a) + tuple(tn_b))


def _fit_compress_rows(tn: "qtn.TensorNetwork", d: int, max_bond: int,
                       gen: torch.Generator, device) -> "qtn.TensorNetwork":
    """One-site variational MPS fit of a row-group TN to bond ``max_bond`` — the
    parent fit-call pattern (``tensor_network_1d_compress(method='fit', bsz=1)``
    with the c128 initial-guess fix), SEEDED (SW-S7): the guess is drawn from
    ``gen`` so every read is replayable. EXACTNESS GUARD (parent convention):
    when every inter-row bond product is already ``<= max_bond`` the TN is
    returned unchanged (compression to a dim >= the exact rank is the identity;
    skipping avoids fit round-off in the exact regime)."""
    if _max_row_bond(tn, d) <= int(max_bond):
        return tn
    site_tags = [_row_tag(u) for u in range(d)]

    def _fill(shape):
        re = torch.randn(*shape, dtype=torch.float64, generator=gen)
        im = torch.randn(*shape, dtype=torch.float64, generator=gen)
        return (re + 1j * im).to(CDTYPE).to(device)

    tn_fit = qtn.TN_matching(tn, max_bond=int(max_bond), site_tags=site_tags,
                             fill_fn=_fill)
    return qtn.tensor_network_1d_compress(
        tn,
        max_bond=int(max_bond),
        cutoff=None,
        method="fit",
        site_tags=site_tags,
        tn_fit=tn_fit,
        bsz=1,
        max_iterations=_FIT_MAX_ITERATIONS,
        tol=_FIT_TOL,
        inplace=False,
    )


def _read_generator(fit_seed: int) -> torch.Generator:
    """One CPU generator per read, seeded — sequential fills within the read are
    then deterministic (the SW-S7 replayability convention)."""
    gen = torch.Generator()
    gen.manual_seed(int(fit_seed))
    return gen


# --------------------------------------------------------------------------- #
# NormCache — reverse-pass boundary MPS over grid columns (double layer)       #
# --------------------------------------------------------------------------- #
class NormCache:
    """Opaque reverse-pass boundary-MPS cache of the double-layer NORM network.

    ``right_envs[c]`` represents columns ``c..d-1`` of the trace (no-op) double
    layer, one tensor per row (tags ``ROW{u}``), bond ``<= R_n``, open indices =
    the ket+bra crossing bond pairs between columns ``c-1`` and ``c``. Built once
    per state snapshot; the cache does NOT track state mutation — a stale cache
    is the caller's bug (rebuild after any selective update / truncation; the
    trajectory loop does).
    """

    def __init__(self, layout, R_n: int, right_envs: dict, fit_seed: int) -> None:
        self.layout = layout
        self.R_n = int(R_n)
        self.right_envs = right_envs  # {c: TensorNetwork}, c = 1..d-1
        self.fit_seed = int(fit_seed)


def norm_cache(state: PepsState, R_n: int, fit_seed: int = 0) -> NormCache:
    """Build the reverse-pass boundary-MPS cache at boundary dim ``R_n`` on the
    double-layer norm network (columns swept ``d-1 -> 1``; each absorption is a
    row-group union followed by the seeded one-site fit to ``R_n``)."""
    layout = state.layout
    d = int(layout.d)
    if int(R_n) < 1:
        raise ValueError(f"R_n must be >= 1 (got {R_n})")
    dev = torch.device(state.device)
    gen = _read_generator(fit_seed)
    right_envs: dict[int, qtn.TensorNetwork] = {}
    env = None
    for c in range(d - 1, 0, -1):
        col = _double_column_tn(state, c, {})
        env = _fit_compress_rows(_merge(col, env), d, int(R_n), gen, dev)
        right_envs[c] = env
    return NormCache(layout, int(R_n), right_envs, int(fit_seed))


# --------------------------------------------------------------------------- #
# expect_double_layer — <psi| (x)_q M_q |psi> (raw, unnormalized)              #
# --------------------------------------------------------------------------- #
def expect_double_layer(state: PepsState, ops: dict, cache: NormCache | None = None,
                        R_n: int | None = None, fit_seed: int = 0) -> complex:
    """RAW ``<psi| (x)_q M_q |psi>`` with per-site ``(3, 3)`` operators (contract
    §3 row "double-layer caps"); sites absent from ``ops`` carry the identity
    (the norm closure). UNNORMALIZED — callers divide by the norm read for a
    probability.

    Contraction routes (the parent convention):
      * ``cache is None and R_n is None`` -> EXACT contraction of the full
        two-layer network (the d3 near-exact instrument; §4 (a)-identity floors);
      * otherwise -> the boundary-MPS route: right environments from ``cache``
        (built at ``R_n`` if absent), forward pass sweeping columns ``0..c_max``
        with the SEEDED one-site fit at the pass dim (SW-S7).
    """
    layout = state.layout
    d = int(layout.d)
    ops = dict(ops or {})
    for pos in ops:
        if pos not in layout.grid:
            raise KeyError(f"op position {pos} not on the layout grid")

    if cache is None and R_n is None:
        tensors = []
        for pos in layout.grid:
            ket, bra = _site_pair(state, pos, ops.get(pos), _row_tag(layout.grid[pos][0]),
                                  open_phys=False)
            tensors.extend((ket, bra))
        return _to_complex(qtn.TensorNetwork(tensors).contract(optimize="auto-hq"))

    r_pass = int(R_n) if R_n is not None else cache.R_n
    if cache is None:
        cache = norm_cache(state, r_pass, fit_seed)
    dev = torch.device(state.device)
    gen = _read_generator(fit_seed)

    # highest column carrying a non-identity op; -1 if none (pure norm read)
    c_max = -1
    for pos in ops:
        c_max = max(c_max, layout.grid[pos][1])

    left = None
    for c in range(0, max(c_max, 0) + 1):
        col = _double_column_tn(state, c, ops)
        left = col if left is None else _fit_compress_rows(_merge(left, col), d,
                                                           r_pass, gen, dev)
    if c_max >= d - 1:
        return _to_complex(left.contract(optimize="auto-hq"))
    env = cache.right_envs.get(max(c_max, 0) + 1)
    if env is None:  # d == 1 single-column grid: no right env exists
        return _to_complex(left.contract(optimize="auto-hq"))
    return _to_complex(_merge(left, env).contract(optimize="auto-hq"))


def norm_read(state: PepsState, cache: NormCache | None = None,
              R_n: int | None = None, fit_seed: int = 0) -> float:
    """``<psi|psi>`` through the same route machinery (the norm leg of every
    §2 read; real part — the imaginary part of a norm read is fp noise)."""
    return expect_double_layer(state, {}, cache=cache, R_n=R_n, fit_seed=fit_seed).real


def expect_site_caps(state: PepsState, caps: dict, cache: NormCache | None = None,
                     R_n: int | None = None, fit_seed: int = 0) -> complex:
    """The PRODUCTION double-layer caps read ``<psi| (x)_q M_q |psi>`` (RAW,
    unnormalized) — the named public seam the SW0 structural cert + the SW6
    b-swap killer read (``caps = {pos: (3,3)}``; absent sites carry the identity;
    ``caps = {}`` reads ``<psi|psi>``). A thin alias of
    :func:`expect_double_layer` (the contract §3 "double-layer caps" name)."""
    return expect_double_layer(state, caps, cache=cache, R_n=R_n, fit_seed=fit_seed)


# --------------------------------------------------------------------------- #
# site_rdm — the double-layer 1-site RDM read (the leak_sample p_k source)     #
# --------------------------------------------------------------------------- #
def site_rdm(state: PepsState, pos: int, cache: NormCache | None = None,
             R_n: int | None = None, fit_seed: int = 0) -> torch.Tensor:
    """The UNNORMALIZED 1-site reduced density matrix ``rho_pos[a, b] =
    sum_rest psi[a, rest] conj(psi[b, rest])`` (``Tr(rho_pos) = <psi|psi>``) —
    the contract §3 ``leak_sample`` row pin: ``p_k`` comes from ONE double-layer
    RDM read + trivial 3x3 traces, never n_kraus full contractions (the
    ``mps_forward._leak_sample`` RDM convention transplanted).

    Boundary route: closed columns left of ``pos`` are fit-compressed; the open
    column (ket/bra physical pair left open as ``_rdmK``/``_rdmB``) is absorbed
    UNCOMPRESSED and closed against the cached right environment by ONE exact
    contraction — the open legs never enter a fit.
    """
    layout = state.layout
    d = int(layout.d)
    pos = int(pos)
    if pos not in layout.grid:
        raise KeyError(f"rdm position {pos} not on the layout grid")

    if cache is None and R_n is None:
        tensors = []
        for p in layout.grid:
            ket, bra = _site_pair(state, p, None, _row_tag(layout.grid[p][0]),
                                  open_phys=(p == pos))
            tensors.extend((ket, bra))
        out = qtn.TensorNetwork(tensors).contract(
            output_inds=(RDM_KET_IND, RDM_BRA_IND), optimize="auto-hq")
        return out.data

    r_pass = int(R_n) if R_n is not None else cache.R_n
    if cache is None:
        cache = norm_cache(state, r_pass, fit_seed)
    dev = torch.device(state.device)
    gen = _read_generator(fit_seed)
    c_pos = layout.grid[pos][1]

    left = None
    for c in range(c_pos):
        col = _double_column_tn(state, c, {})
        left = col if left is None else _fit_compress_rows(_merge(left, col), d,
                                                           r_pass, gen, dev)
    merged = _merge(left, _double_column_tn(state, c_pos, {}, open_pos=pos))
    env = cache.right_envs.get(c_pos + 1)
    if env is not None:
        merged = _merge(merged, env)
    out = merged.contract(output_inds=(RDM_KET_IND, RDM_BRA_IND), optimize="auto-hq")
    return out.data


# --------------------------------------------------------------------------- #
# Two-term stab read (N and M) + the Born p0 (contract §2 born_read_stab row)  #
# --------------------------------------------------------------------------- #
def stab_site_ops(paulis: dict, b: float, arm: str, device) -> dict:
    """The per-site parity operators ``M_q`` of the two-term decomposition:
    ``M_q = diag(1, -1, d2)`` on Z sites, ``H . diag(1, -1, d2) . H`` on X sites
    (the F2 rotate-measure-rotate identity; leaked levels H-inert; ``d2`` the
    arm's leaked weight — SF4). LOCAL formulas (D4)."""
    d2 = leaked_weight(b, arm)
    diag = torch.zeros((QUTRIT, QUTRIT), dtype=CDTYPE, device=device)
    diag[0, 0] = 1.0
    diag[1, 1] = -1.0
    diag[2, 2] = d2
    h = qutrit_gate("H", device)
    hx = h @ diag @ h
    ops = {}
    for site, p in paulis.items():
        kind = str(p).upper()
        if kind == "X":
            ops[int(site)] = hx
        elif kind == "Z":
            ops[int(site)] = diag
        else:
            raise ValueError(f"stabilizer support must be 'X'|'Z' (got {p!r} at {site})")
    return ops


def born_read_stab(state: PepsState, paulis: dict, b: float, arm: str, *,
                   cache_n: NormCache | None = None, cache_x: NormCache | None = None,
                   R_n: int | None = None, R_x: int | None = None,
                   fit_seed: int = 0) -> tuple[float, float, float]:
    """The two-term read ``(N, M, p0)`` (contract §2 ``born_read_stab`` row):
    ``N = <psi|psi>`` (norm pass, dim ``R_n``), ``M = <psi| (x)_q M_q |psi>``
    (sample pass, dim ``R_x``), ``p0 = clamp((1/2 N + 1/2 M) / N)`` — p0 from
    ``e`` with ``s = 0`` (the s-sign is +1 on outcome 0). Exact route when the
    corresponding cache/R args are both None. q0 + q1 = N holds IDENTICALLY
    (SF9) — no closure is read here; §6.2 instruments are separate functions."""
    ops = stab_site_ops(paulis, b, arm, torch.device(state.device))
    N = expect_double_layer(state, {}, cache=cache_n, R_n=R_n, fit_seed=fit_seed).real
    M = expect_double_layer(state, ops, cache=cache_x, R_n=R_x, fit_seed=fit_seed).real
    if not N > NUMERICAL_ZERO:
        raise RuntimeError(f"born_read_stab: nonpositive norm {N:.6e} (state collapsed)")
    p0 = min(1.0, max(0.0, (0.5 * N + 0.5 * M) / N))
    return float(N), float(M), float(p0)


# --------------------------------------------------------------------------- #
# §6.2 per-read accuracy instruments (cross-route + chi_b doubling)            #
# --------------------------------------------------------------------------- #
def branch_norm_sq(state: PepsState, stab_tt: SingleWireStabTT, *,
                   R_n: int | None = None, fit_seed: int = 0) -> float:
    """``||sqrt(E_s) psi||^2`` by the BRANCH-NORM route (§6.2): apply the TT to a
    COPY of the state, contract the double-layer norm — an INDEPENDENT
    contraction path through a DIFFERENT network (the caps route never touches
    the TT; independence is the instrument's design). Exact route at
    ``R_n=None``; no cache is accepted (the grown copy invalidates any)."""
    probe = state.copy()
    apply_stab_branch(probe, stab_tt)
    return norm_read(probe, R_n=R_n, fit_seed=fit_seed)


def cross_route_q1(state: PepsState, paulis: dict, b: float, arm: str, *,
                   R_n: int | None = None, R_x: int | None = None,
                   fit_seed: int = 0) -> dict:
    """The §6.2 cross-route residual on one Born read: ``q1`` by (i) the caps
    two-term route ``1/2 N - 1/2 M`` and (ii) the branch-norm route
    ``||sqrt(E_1) psi||^2``; residual ``|q1_caps - q1_norm| / N``. Returns the
    ledger-ready entry (the SW8 "ledgers close" condition checks these against
    the §6.2 floor table — d3: <= 1e-10 every read; d5 in-run: <= 1e-6)."""
    N, M, _p0 = born_read_stab(state, paulis, b, arm, R_n=R_n, R_x=R_x,
                               fit_seed=fit_seed)
    q1_caps = 0.5 * N - 0.5 * M
    tt = stab_tt_singlewire(paulis, 1, b, arm, state.layout, state.device)
    q1_norm = branch_norm_sq(state, tt, R_n=R_n, fit_seed=fit_seed)
    return {
        "kind": "cross_route",
        "q1_caps": float(q1_caps),
        "q1_norm": float(q1_norm),
        "N": float(N),
        "resid_rel": float(abs(q1_caps - q1_norm) / N),
        "tt_ranks": tuple(int(r) for r in tt.ranks),
    }


def chib_doubling_delta(state: PepsState, paulis: dict, b: float, arm: str,
                        chi_b: int, *, fit_seed: int = 0) -> dict:
    """The §6.2 chi_b-doubling delta ``|M(chi_b) - M(2 chi_b)| / N`` — a
    CONSISTENCY estimator, not an error bound (RT2: a false plateau is possible;
    the evolved-probe R-sweep leg mitigates). Returns the ledger-ready entry."""
    ops = stab_site_ops(paulis, b, arm, torch.device(state.device))
    m_lo = expect_double_layer(state, ops, R_n=int(chi_b), fit_seed=fit_seed).real
    m_hi = expect_double_layer(state, ops, R_n=2 * int(chi_b), fit_seed=fit_seed).real
    n_hi = expect_double_layer(state, {}, R_n=2 * int(chi_b), fit_seed=fit_seed).real
    if not n_hi > NUMERICAL_ZERO:
        raise RuntimeError(f"chib_doubling_delta: nonpositive norm {n_hi:.6e}")
    return {
        "kind": "chib_doubling",
        "chi_b": int(chi_b),
        "M_chi": float(m_lo),
        "M_2chi": float(m_hi),
        "N": float(n_hi),
        "delta_rel": float(abs(m_lo - m_hi) / n_hi),
    }


# --------------------------------------------------------------------------- #
# Terminal-readout effects + the support-only exact-P(obs) seam                #
# --------------------------------------------------------------------------- #
def terminal_effect_pair(b: float, device) -> tuple[torch.Tensor, torch.Tensor]:
    """The pinned per-site terminal POVM pair (contract §3 ``terminal_readout``
    row): ``F1 = |1><1| + b |2><2|``, ``F0 = |0><0| + (1-b) |2><2|``
    (``F0 + F1 = I``; ``F0 - F1 = diag(1, -1, 1-2b)``, consistent with F2)."""
    bval = float(b)
    if not 0.0 <= bval <= 1.0:
        raise ValueError(f"readout bias b must be in [0, 1] (got {bval})")
    f1 = torch.zeros((QUTRIT, QUTRIT), dtype=CDTYPE, device=device)
    f1[1, 1] = 1.0
    f1[2, 2] = bval
    f0 = torch.zeros((QUTRIT, QUTRIT), dtype=CDTYPE, device=device)
    f0[0, 0] = 1.0
    f0[2, 2] = 1.0 - bval
    return f0, f1


def terminal_collapse_diag(bit: int, b: float, device) -> torch.Tensor:
    """The ``sqrt(F_bit)`` collapse operator (the ``mps_forward`` hard2 value
    contract): bit 1 -> ``diag(0, 1, sqrt(b))``; bit 0 ->
    ``diag(1, 0, sqrt(1-b))``. Applied as a 1-site op; the caller renormalizes."""
    bval = float(b)
    if int(bit) == 1:
        vec = torch.tensor([0.0, 1.0, bval ** 0.5], dtype=CDTYPE, device=device)
    else:
        vec = torch.tensor([1.0, 0.0, (1.0 - bval) ** 0.5], dtype=CDTYPE, device=device)
    return torch.diag(vec)


def _terminal_site_effects(logical: dict, isx: dict, b: float, device) -> dict:
    """Per-site terminal effect pairs ``{q: (E0_q, E1_q)}`` over the SORTED
    logical support, X-flagged sites H-CONJUGATED (``E_c = H F_c H``) — the ONE
    effect construction the exact-P(obs) seam composes through (site-local
    conjugation is value-identical to the sampling arm's up-front state
    rotation: disjoint sites, ``Tr(H rho H . F) = Tr(rho . H F H)``)."""
    f0, f1 = terminal_effect_pair(b, device)
    h = qutrit_gate("H", device)
    support = sorted(int(q) for q in logical)
    if not support:
        raise ValueError("terminal effects: empty logical support")
    effects: dict[int, tuple[torch.Tensor, torch.Tensor]] = {}
    for q in support:
        if isx.get(q, 0):
            effects[q] = (h @ f0 @ h, h @ f1 @ h)
        else:
            effects[q] = (f0, f1)
    return effects


def terminal_obs_prob(state: PepsState, logical: dict, isx: dict, b: float,
                      m: int) -> float:
    """EXACT ``P(obs = 1)`` — the SUPPORT-ONLY enumeration seam, retained
    DISTRIBUTION-LEVEL ONLY (contract §3: valid because product-POVM outcome
    marginals on disjoint sites are unchanged by measuring the complement — an
    (a) one-line theorem; **NEVER a byte-level referee** — the per-shot sampling
    law reads ALL n_data sites, RT1-B2).

    Enumerates the ``2^w`` outcome tuples over the sorted logical support, sums
    the exact double-layer joint weights ``<psi| (x)_q E_{c_q} |psi>`` over the
    tuples whose parity XOR ``m`` equals 1, normalized by ``<psi|psi>``.
    UNCLAMPED (a value outside [0, 1] is exactly the discrepancy the seam must
    expose). The state is NOT mutated; no draw occurs. Exact route only.
    """
    device = torch.device(state.device)
    effects = _terminal_site_effects(logical, isx, b, device)
    support = list(effects)
    w = len(support)

    tr = norm_read(state)
    if not tr > NUMERICAL_ZERO:
        raise RuntimeError(f"terminal_obs_prob: nonpositive norm {tr:.6e}")

    target = 1 ^ (int(m) & 1)  # parity value making obs = parity XOR m equal 1
    total = 0.0
    for mask in range(1 << w):
        parity = bin(mask).count("1") & 1
        if parity != target:
            continue
        ops = {q: effects[q][(mask >> i) & 1] for i, q in enumerate(support)}
        total += expect_double_layer(state, ops).real
    return float(total / tr)

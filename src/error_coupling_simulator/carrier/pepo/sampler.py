from __future__ import annotations

"""Boundary-MPS contraction, ``Tr(rho * Pi)`` site caps, and Born sampling for the
rung-1 d3 PEPO engine (builder A3; contract
``docs/nonpauli_teacher/pepo_engine_rung1_contract.md`` v4.2 §3, sampler rows).

The state object is :class:`~.layout.PepoState`: a quimb ``TensorNetwork`` of rank<=5
site tensors on the (u, v) grid, one per data qutrit, physical leg = the FUSED d^2 = 9
vectorized index named ``k{pos}`` with the pinned ROW-MAJOR vec convention

    ``k = 3 * t_ket + t_bra``           (contract §2; every superoperator uses it).

This module implements the s3 registry rows owned by A3:

  * :func:`pepo_trace` — exact ``Tr(rho)`` (the C1 invariant read).
  * :func:`norm_cache` / :class:`NormCache` — the Rudolph–Tindall (arXiv:2507.11424,
    reading note ``docs/papers/reading_notes/rudolph_tindall_gpu_peps_2507.11424.md``)
    REVERSE-pass boundary-MPS over grid COLUMNS, one-site variational MPS-MPO fitting,
    boundary dim ``R_n`` — cached right-environments of the SINGLE-layer trace network
    (the PEPO's ``Tr(rho * Pi)`` is single-layer; no doubled norm network exists here).
  * :func:`expect_site_caps` — general single-site expectation caps (derivation in its
    docstring; a cap is an EXPECTATION functional, never ``M (x) M.conj()``).
  * :func:`stab_expectation` — the pinned two-term ``E_s`` decomposition
    ``Tr(E_s rho) = 1/2 Tr(rho) + 1/2 (-1)^s Tr(rho * (x)_q M_q)`` (contract §3).
  * :func:`born_sample_round` — sequential conditional Born sampling of one round's
    stabilizers, SELECTIVE ``sqrt(E_s)`` update via ``dynamics.apply_stab_branch`` +
    ``dynamics.ntu_truncate``, renormalize + ledger, negativity witness on every draw.
  * :func:`terminal_readout_obs` — the pinned obs law VERBATIM (logical support only,
    ``isx`` sites H-conjugated, ``F1 = |1><1| + b|2><2|``, ``F0 = |0><0| + (1-b)|2><2|``,
    parity XOR ``m``).
  * :func:`terminal_readout_obs_prob` — the EXACT ``P(obs = 1)`` composed through the
    SAME per-site effect construction the sampling path uses (contract §3, v4.2
    EXACT-PROBABILITY SEAM — the engine-side killer seam for the G1.1 b-swap killer).
  * :func:`s_to_det` / :func:`det_to_s` — the ``seam.py`` detector-fold conventions
    (``det(0,j) = s(0,j)``; ``det(r,j) = s(r,j) XOR s(r-1,j)``) and the pinned inversion
    ``s(r,j) = XOR_{r'<=r} det(r',j)``.
  * :func:`negativity_witness` / :class:`C3Stats` — the C3 rules (i)/(ii) vs the
    measured G1.9 bar; rule (ii) rides the run-level O(1) :class:`C3Stats` accumulator
    (v4.2); raises ``RuntimeError("C3_STOP: ...")`` on trip unless ``log_only`` (the
    v4.2 C3 arm-scoping: a would-trip becomes a ``kind='c3_would_trip'`` ledger entry —
    the S9 finding record). Positivity is NEVER assumed (§2).

Column convention (algorithm-internal, documented not contract-pinned): a boundary-MPS
"column" ``c`` is the set of sites with grid coordinate ``v == c``; the MPS runs over
rows ``u = 0..d-1`` (site tags ``ROW{u}``). Any consistent axis choice is valid — the
contraction value is axis-independent; this one is fixed here for determinism.

GPU + complex128 (S8): every cap/effect tensor is created ``torch.complex128`` on
``state.device`` (devices passed in, never chosen here). No pytest/GPU execution happens
at import; ``dynamics`` is imported lazily inside :func:`born_sample_round`.
"""

import numpy as np
import torch

import quimb.tensor as qtn

from ...numerics import NUMERICAL_ZERO

CDTYPE = torch.complex128

#: The registered G1.9 Weyl-scale FLOOR for the negativity bar (contract §4 G1.9:
#: bar = max(10x the measured single-cut-proxy |lambda_min|, 4.8e-4); class (b)).
#: The MEASURED bar from the G1.9-pre run supersedes this floor — every witness-bearing
#: entry point takes an explicit ``g19_bar``; this constant is only the default when the
#: caller has not yet wired the measured value (the floor term of the max() either way).
G19_BAR_WEYL_FLOOR = 4.8e-4

#: One-site variational fit constants ((c)-class design constants; the fitting is the
#: Rudolph–Tindall one-site ALS pattern, quimb `tensor_network_1d_compress(method="fit",
#: bsz=1)`).
_FIT_MAX_ITERATIONS = 64
_FIT_TOL = NUMERICAL_ZERO


# --------------------------------------------------------------------------- #
# Small helpers: qutrit H, cap vectors, tensor access                          #
# --------------------------------------------------------------------------- #
def _qutrit_hadamard(device) -> torch.Tensor:
    """Hadamard on the computational ``{|0>, |1>}`` subspace, identity on ``|2>``
    (the F2 convention: leaked levels are H-inert). Built locally BY FORMULA so the
    engine stays referee-independent (anti-circularity, prereg §4)."""
    h = torch.zeros((3, 3), dtype=CDTYPE, device=device)
    inv2 = 1.0 / (2.0 ** 0.5)
    h[0, 0] = inv2
    h[0, 1] = inv2
    h[1, 0] = inv2
    h[1, 1] = -inv2
    h[2, 2] = 1.0
    return h


def _trace_cap(device) -> torch.Tensor:
    """The trace cap on the fused leg: ``t[k] = delta_{t_ket, t_bra}`` i.e.
    ``t[3a + b] = [a == b]`` — contracting it with a site's ``k`` index performs the
    partial trace over that site (``Tr_site rho``)."""
    t = torch.zeros(9, dtype=CDTYPE, device=device)
    t[0] = 1.0  # (0,0)
    t[4] = 1.0  # (1,1)
    t[8] = 1.0  # (2,2)
    return t


def _cap_vector(cap, device) -> torch.Tensor:
    """Normalize a user cap to the length-9 fused-leg cap COVECTOR.

    DERIVATION (the pinned k = 3*t_ket + t_bra ROW-MAJOR convention). The site tensor's
    fused component at ``k = 3a + b`` carries the density-operator component
    ``rho[..., a, b] ~ |a><b|`` (``a`` = ket/row, ``b`` = bra/column). For a single-site
    operator ``M``:

        ``Tr(rho * M) = sum_{a,b} rho[a, b] * M[b, a] = sum_k vec(M^T)[k] * rho_k``

    so the cap covector for a ``(3, 3)`` op ``M`` is ``vec(M^T)`` in ROW-MAJOR vec —
    entry ``k = 3a + b`` holds ``M[b, a]``. NO complex conjugate appears (a cap is an
    EXPECTATION functional contracted with the fused index, never a two-sided
    ``M (x) M.conj()`` superoperator apply). Consistency check: lifting left-mult-by-M
    to the fused leg (row-major vec: ``vec(M rho N) = (M (x) N^T) vec(rho)``) and closing
    with the trace cap gives ``t^T (M (x) I) = vec(M^T)`` — the same covector.

    Accepted inputs (contract §3 "general single-site fused operators"):
      * ``(3, 3)`` operator ``M``            -> ``vec(M^T)``;
      * length-9 1-D vector ``d``            -> DIAGONAL fused superoperator (elementwise
        multiplier on the fused leg): cap ``= t * d`` (``t`` the trace cap) — the natural
        carrier for diagonal ``sqrt(E)``-style weights;
      * length-81 tensor ``S`` (reshaped ``(9, 9)``, row-major, ``k_out``/``k_in`` both in
        the pinned fused convention) -> full fused-leg superoperator: cap ``= t^T S``
        (apply the superop, then trace).
    Anything else raises.
    """
    v = torch.as_tensor(cap, dtype=CDTYPE, device=device)
    t = _trace_cap(device)
    if v.ndim == 2 and v.shape == (3, 3):
        return v.transpose(0, 1).reshape(9).contiguous()
    if v.ndim == 1 and v.numel() == 9:
        return (t * v).contiguous()
    if v.numel() == 81:
        s = v.reshape(9, 9)
        return torch.einsum("k,kj->j", t, s).contiguous()
    raise ValueError(
        f"cap must be a (3,3) site op, a length-9 fused diagonal, or a length-81 fused "
        f"superoperator; got shape {tuple(v.shape)}")


def _site_tensor(state, pos: int):
    """The unique site tensor tagged ``Q{pos}`` (contract §2 tag convention)."""
    ts = state.tn.select_tensors(f"Q{int(pos)}", which="all")
    if len(ts) != 1:
        raise RuntimeError(f"expected exactly one tensor tagged Q{pos}, found {len(ts)}")
    return ts[0]


def _to_complex(x) -> complex:
    """Scalar contraction output (0-dim torch tensor or python scalar) -> complex."""
    if hasattr(x, "item"):
        return complex(x.item())
    return complex(x)


def _columns(layout) -> int:
    """Number of grid columns (= d; the grid is asserted d x d by the layout)."""
    return int(layout.d)


def _row_tag(u: int) -> str:
    return f"ROW{int(u)}"


def _capped_column_tn(state, c: int, caps: dict) -> "qtn.TensorNetwork":
    """Column ``c`` (sites with grid v == c) with each fused leg closed by its cap
    (``caps.get(pos, trace-cap)``), one tensor per row ``u``, tagged ``ROW{u}``."""
    layout = state.layout
    d = _columns(layout)
    tensors = []
    for u in range(d):
        pos = layout.pos_at[(u, c)]
        site = _site_tensor(state, pos)
        cap = caps.get(pos)
        vec = _trace_cap(state.device) if cap is None else _cap_vector(cap, state.device)
        cap_t = qtn.Tensor(vec, inds=(f"k{pos}",))
        tc = qtn.tensor_contract(site, cap_t, preserve_tensor=True)
        tc.drop_tags()
        tc.add_tag(_row_tag(u))
        tensors.append(tc)
    return qtn.TensorNetwork(tensors)


def _absorb_rows(tn_a: "qtn.TensorNetwork", tn_b: "qtn.TensorNetwork", d: int) -> "qtn.TensorNetwork":
    """Row-wise contraction of two column-like TNs (matched by ``ROW{u}`` tags): the
    per-row pair shares the crossing bond(s); the result is again one tensor per row."""
    tensors = []
    for u in range(d):
        ta = tn_a.select_tensors(_row_tag(u), which="all")
        tb = tn_b.select_tensors(_row_tag(u), which="all")
        tc = qtn.tensor_contract(*ta, *tb, preserve_tensor=True)
        tc.drop_tags()
        tc.add_tag(_row_tag(u))
        tensors.append(tc)
    return qtn.TensorNetwork(tensors)


def _max_row_bond(tn: "qtn.TensorNetwork", d: int) -> int:
    """Largest total bond dimension (product over shared inds) between consecutive rows."""
    mx = 1
    for u in range(d - 1):
        ts_a = tn.select_tensors(_row_tag(u), which="all")
        ts_b = tn.select_tensors(_row_tag(u + 1), which="all")
        shared = set()
        for a in ts_a:
            for b in ts_b:
                shared |= set(a.inds) & set(b.inds)
        dim = 1
        for ix in shared:
            dim *= tn.ind_size(ix)
        mx = max(mx, dim)
    return int(mx)


def _fit_compress_rows(tn: "qtn.TensorNetwork", d: int, max_bond: int) -> "qtn.TensorNetwork":
    """One-site variational MPS fit of a row-chain TN to bond dim ``max_bond`` (the
    Rudolph–Tindall MPS-MPO fitting step; quimb ``tensor_network_1d_compress`` with
    ``method='fit'``, ``bsz=1``). EXACTNESS GUARD: when every inter-row bond is already
    ``<= max_bond`` the chain IS an MPS of the requested dim and is returned unchanged
    (compression to a dim >= the exact rank is the identity; skipping it avoids fit
    round-off in the exact regime)."""
    if _max_row_bond(tn, d) <= int(max_bond):
        return tn
    site_tags = [_row_tag(u) for u in range(d)]
    # BACKEND-MATCHED initial guess (v4.2 fix): quimb's default random guess is
    # numpy-CPU float64, which poisons the torch-cuda-complex128 fit; build the guess
    # explicitly on the input TN's device/dtype and hand it to the fit as ``tn_fit``.
    # Signatures verified in the installed quimb 1.14.0:
    # ``TN_matching(tn, max_bond, site_tags=None, fill_fn=None, dtype=None,
    # **randn_opts)`` with ``fill_fn(shape) -> array``
    # (quimb/tensor/tensor_builder.py:4062); ``tensor_network_1d_compress`` forwards
    # ``tn_fit`` to ``tensor_network_1d_compress_fit(..., tn_fit=None, ...)``
    # (quimb/tensor/tn1d/compress.py:2239-2243).
    ref = next(iter(tn.tensors)).data
    device = ref.device

    def _fill(shape):
        return (torch.randn(*shape, dtype=torch.float64)
                + 1j * torch.randn(*shape, dtype=torch.float64)).to(CDTYPE).to(device)

    tn_fit = qtn.TN_matching(
        tn,
        max_bond=int(max_bond),
        site_tags=site_tags,
        fill_fn=_fill,
    )
    out = qtn.tensor_network_1d_compress(
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
    return out


# --------------------------------------------------------------------------- #
# pepo_trace — the C1 invariant read (exact)                                   #
# --------------------------------------------------------------------------- #
def pepo_trace(state) -> complex:
    """EXACT ``Tr(rho)``: close every fused leg with the trace cap and contract the
    whole (single-layer) network with an optimized path. This is the C1 invariant read
    (contract §2: ``pepo_trace(state) == 1`` within the logged trace-shift ledger after
    every round); the boundary-MPS route (:func:`norm_cache` + :func:`expect_site_caps`)
    is the production/truncated instrument — this one is the exact anchor at d3 scale.
    """
    layout = state.layout
    tensors = []
    for pos in layout.grid:
        site = _site_tensor(state, pos)
        cap_t = qtn.Tensor(_trace_cap(state.device), inds=(f"k{pos}",))
        tensors.append(qtn.tensor_contract(site, cap_t, preserve_tensor=True))
    tn = qtn.TensorNetwork(tensors)
    return _to_complex(tn.contract(optimize="auto-hq"))


# --------------------------------------------------------------------------- #
# NormCache — Rudolph–Tindall reverse-pass boundary MPS over grid columns      #
# --------------------------------------------------------------------------- #
class NormCache:
    """Opaque reverse-pass boundary-MPS cache (produced/consumed only in this module).

    ``right_envs[c]`` is the boundary MPS (one tensor per row, tags ``ROW{u}``, bond dim
    ``<= R_n``) representing columns ``c..d-1`` of the TRACE-capped single-layer network,
    with open indices = the crossing bonds between columns ``c-1`` and ``c`` — the
    Rudolph–Tindall reverse pass (their §II-C norm-network pre-computation), adapted to
    the SINGLE-layer PEPO trace network. Built once per state snapshot; the cache does
    NOT track state mutation (a stale cache is the caller's bug — rebuild after any
    selective update / truncation; :func:`born_sample_round` does).
    """

    def __init__(self, layout, R_n: int, right_envs: dict) -> None:
        self.layout = layout
        self.R_n = int(R_n)
        self.right_envs = right_envs  # {c: TensorNetwork}, c = 1..d-1


def norm_cache(state, R_n: int) -> NormCache:
    """Build the reverse-pass boundary-MPS cache at boundary dim ``R_n`` (contract §3:
    "Rudolph–Tindall reverse-pass boundary-MPS over grid columns (one-site fitting,
    dim R_n), cached once per state"). Columns are swept ``d-1 -> 1``; each absorption
    is row-wise contraction followed by the one-site variational fit to ``R_n``."""
    layout = state.layout
    d = _columns(layout)
    if int(R_n) < 1:
        raise ValueError(f"R_n must be >= 1 (got {R_n})")
    right_envs: dict[int, qtn.TensorNetwork] = {}
    env = None
    for c in range(d - 1, 0, -1):
        col = _capped_column_tn(state, c, {})
        target = col if env is None else _absorb_rows(col, env, d)
        env = _fit_compress_rows(target, d, int(R_n))
        right_envs[c] = env
    return NormCache(layout, int(R_n), right_envs)


def expect_site_caps(state, caps: dict, cache: NormCache | None = None,
                     R_n: int | None = None) -> complex:
    """``Tr(rho * (x)_q Pi_q)`` with GENERAL single-site caps (contract §3 registry row).

    ``caps`` maps engine position -> a ``(3, 3)`` site operator, a length-9 fused
    diagonal, or a length-81 fused superoperator (see :func:`_cap_vector` for the pinned
    derivation); sites ABSENT from ``caps`` get the trace cap (partial trace). Returns
    the RAW (unnormalized) expectation — callers normalize by ``Tr(rho)`` when they need
    a probability.

    Contraction routes:
      * ``cache is None and R_n is None`` -> EXACT contraction (the d3 dense-equality
        referee route, 1e-10 bar per the registry row);
      * otherwise -> the boundary-MPS route: right environments from ``cache`` (built at
        ``R_n`` if absent), forward pass sweeping columns ``0..c_max`` with the same
        one-site fit at the pass dim (``R_n`` if given else ``cache.R_n``) — the
        Rudolph–Tindall forward pattern on the single-layer network.
    """
    layout = state.layout
    d = _columns(layout)
    caps = dict(caps or {})
    for pos in caps:
        if pos not in layout.grid:
            raise KeyError(f"cap position {pos} not on the layout grid")

    if cache is None and R_n is None:
        # exact route: full capped network, optimized path
        tensors = []
        for pos in layout.grid:
            site = _site_tensor(state, pos)
            cap = caps.get(pos)
            vec = _trace_cap(state.device) if cap is None else _cap_vector(cap, state.device)
            cap_t = qtn.Tensor(vec, inds=(f"k{pos}",))
            tensors.append(qtn.tensor_contract(site, cap_t, preserve_tensor=True))
        return _to_complex(qtn.TensorNetwork(tensors).contract(optimize="auto-hq"))

    if cache is None:
        cache = norm_cache(state, int(R_n))
    r_pass = int(R_n) if R_n is not None else cache.R_n

    # highest column carrying a non-trace cap; -1 if none (pure trace)
    c_max = -1
    for pos in caps:
        c_max = max(c_max, layout.grid[pos][1])

    left = None
    for c in range(0, max(c_max, 0) + 1):
        col = _capped_column_tn(state, c, caps)
        left = col if left is None else _fit_compress_rows(_absorb_rows(left, col, d), d, r_pass)
    if c_max >= d - 1:
        return _to_complex(left.contract(optimize="auto-hq"))
    env = cache.right_envs.get(max(c_max, 0) + 1)
    if env is None:  # d == 1 single-column grid: no right env exists
        return _to_complex(left.contract(optimize="auto-hq"))
    closed = _absorb_rows(left, env, d)
    return _to_complex(closed.contract(optimize="auto-hq"))


# --------------------------------------------------------------------------- #
# stab_expectation — the pinned two-term E_s decomposition (contract §3)       #
# --------------------------------------------------------------------------- #
def _arm_leaked_weight(b: float, arm: str) -> float:
    """The per-site leaked parity weight ``d_q(leaked)`` per measurement arm (the F2
    normative table, ``QutritDM._povm_diag_weight``): A/C -> ``1-2b``; B1 -> ``+1``;
    B2 -> ``-1``; unknown raises."""
    a = str(arm).upper()
    if a in ("A", "C"):
        bval = float(b)
        if not 0.0 <= bval <= 1.0:
            raise ValueError(f"readout bias b must be in [0, 1] (got {bval})")
        return 1.0 - 2.0 * bval
    if a == "B1":
        return 1.0
    if a == "B2":
        return -1.0
    raise ValueError(f"unknown measurement arm {arm!r} (expected A, C, B1 or B2)")


def _stab_site_ops(paulis: dict, b: float, arm: str, device) -> dict:
    """The per-site parity operators ``M_q`` of the two-term decomposition:
    ``M_q = diag(1, -1, d2)`` on Z sites, ``H . diag(1, -1, d2) . H`` on X sites
    (contract §3: H-conjugated M_q on X sites — the F2 rotate-measure-rotate identity
    ``Tr(H rho H . D) = Tr(rho . H D H)``; leaked levels H-inert)."""
    d2 = _arm_leaked_weight(b, arm)
    diag = torch.zeros((3, 3), dtype=CDTYPE, device=device)
    diag[0, 0] = 1.0
    diag[1, 1] = -1.0
    diag[2, 2] = d2
    h = _qutrit_hadamard(device)
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


def stab_expectation(state, paulis: dict, outcome: int, b: float, arm: str,
                     cache: NormCache | None = None, R_n: int | None = None) -> float:
    """RAW ``Tr(E_s rho)`` via the pinned two-term decomposition (contract §3):

        ``Tr(E_s rho) = 1/2 Tr(rho) + 1/2 (-1)^s Tr(rho * (x)_q M_q)``

    with ``M_q = diag(1, -1, d2)`` on Z sites and ``H diag(1, -1, d2) H`` on X sites
    (``d2`` the arm's leaked weight; F2). UNNORMALIZED: divide by ``Tr(rho)`` for the
    conditional Born probability. The arm-C leak-flag dephase does not alter this
    expectation (``M_q`` is block-diagonal in the leak flag, so cross-sector coherences
    never enter — the referee's own arm-C docstring notes ``P(s)`` identical to arm A);
    arm-C's dephase is APPLIED BY DYNAMICS (contract §3 ``stab_channel_tt`` row, v4.2
    ARM-C DEPHASE paragraph: the per-site fused-leg diagonal mask — entry 1 iff
    ``(t>=2) == (t'>=2)`` — applied on the support before the TT, dephase-then-``E_s``
    order), so it acts in the selective-update path, not in this expectation read.

    Both terms ride the same contraction route (exact when ``cache``/``R_n`` are both
    None, boundary-MPS otherwise) so the production G1.2 read goes through the site-cap
    path end to end (contract §4 G1.2).
    """
    ops = _stab_site_ops(paulis, b, arm, torch.device(state.device))
    tr = expect_site_caps(state, {}, cache=cache, R_n=R_n)
    term = expect_site_caps(state, ops, cache=cache, R_n=R_n)
    sign = 1.0 if (int(outcome) & 1) == 0 else -1.0
    return float(0.5 * tr.real + 0.5 * sign * term.real)


# --------------------------------------------------------------------------- #
# negativity_witness — C3 rules (i)/(ii) (contract §4 G1.9, v4.2)              #
# --------------------------------------------------------------------------- #
class C3Stats:
    """Run-level O(1) accumulator for C3 rule (ii) (v4.2 fix — the per-call ledger
    rescan made the witness O(N^2) over a run's Born draws). The RUN DRIVER owns one
    instance per run and threads it through every witness-bearing entry point; each
    Born draw updates it in O(1) (``count += 1``;
    ``sum_neg_mass += max(0, -q_raw) / Tr(rho)``), and rule (ii) reads
    ``sum_neg_mass / count`` — the same mean-over-all-draws the ledger rescan computed,
    without the rescan. The per-draw ledger entries are unchanged (they remain the
    audit record; the accumulator is the evaluator)."""

    __slots__ = ("count", "sum_neg_mass")

    def __init__(self) -> None:
        self.count = 0
        self.sum_neg_mass = 0.0

    @property
    def mean_neg_mass(self) -> float:
        """Mean per-draw normalized negative Born mass over the run so far."""
        return self.sum_neg_mass / self.count if self.count else 0.0


def negativity_witness(q_raw: float, tr: float, ledger: list, g19_bar: float,
                       stats: "C3Stats | None" = None, log_only: bool = False) -> None:
    """The C3 positivity witness (non-optional, contract §2/§4 G1.9 — v4.2):

      (i)  any SINGLE raw Born weight ``q_raw < -(10 * g19_bar)``  =>  STOP;
      (ii) the MEAN over ALL Born draws of the run (per-draw, not per-shot-aggregated)
           of ``max(0, -q_raw) / Tr(rho)``  ``> g19_bar``          =>  STOP.

    Every call logs one PER-DRAW ledger entry (``kind='born_negativity'``) carrying the
    raw weight, the parent trace, and the normalized negative mass. Rule (ii) is
    evaluated on the run-level :class:`C3Stats` accumulator ``stats``, updated here in
    O(1) per draw (v4.2 — this replaces the O(N^2) per-call ledger rescan; the mean is
    identical). BACKWARD-COMPAT: when ``stats`` is ``None``, rule (i) is still
    evaluated on the current draw, but rule (ii) is SKIPPED — rule (ii) is a RUN-level
    rule and needs the run accumulator; without it the only alternative would be the
    ledger rescan this fix removes, so stats-less calls are per-draw-only by design
    (run drivers must pass ``stats``).

    ``log_only`` (v4.2 C3 arm-scoping, contract §4 G1.1 — the R=4 exerciser arm's Born
    weights carry boundary-ESTIMATOR error the state-lambda_min-calibrated bar cannot
    distinguish from negativity): when True a would-trip of rule (i) or (ii) does NOT
    raise; it appends a ``kind='c3_would_trip'`` ledger entry with the values — the S9
    finding record, reported in the run output, never an abort. The R=16 asserted arm
    keeps full C3 STOP semantics (``log_only=False``).

    ``g19_bar`` is the MEASURED G1.9 bar
    (``max(10x the G1.9-pre |lambda_min|, 4.8e-4)`` — class (b)); a trip raises
    ``RuntimeError('C3_STOP: ...')`` and is a finding feeding the LPDO decision (S9),
    never a silently-tolerated event.
    """
    bar = float(g19_bar)
    if not bar > 0.0:
        raise ValueError(f"g19_bar must be positive (got {g19_bar})")
    q = float(q_raw)
    t = float(tr)
    denom = t if abs(t) > NUMERICAL_ZERO else NUMERICAL_ZERO
    neg_mass = max(0.0, -q) / denom
    ledger.append({
        "kind": "born_negativity",
        "q_raw": q,
        "tr": t,
        "neg_mass": neg_mass,
        "g19_bar": bar,
    })
    if stats is not None:
        stats.count += 1
        stats.sum_neg_mass += neg_mass
    if q < -(10.0 * bar):
        msg = (f"C3_STOP: single raw Born weight q_raw={q:.6e} < -(10 x G1.9 bar) = "
               f"{-(10.0 * bar):.6e} (rule i)")
        if log_only:
            ledger.append({
                "kind": "c3_would_trip",
                "rule": "i",
                "q_raw": q,
                "tr": t,
                "neg_mass": neg_mass,
                "g19_bar": bar,
                "threshold": -(10.0 * bar),
                "message": msg,
            })
        else:
            raise RuntimeError(msg)
    if stats is not None:
        mean_neg = stats.mean_neg_mass
        if mean_neg > bar:
            msg = (f"C3_STOP: mean per-draw negative Born mass {mean_neg:.6e} > G1.9 "
                   f"bar {bar:.6e} over {stats.count} draws (rule ii)")
            if log_only:
                ledger.append({
                    "kind": "c3_would_trip",
                    "rule": "ii",
                    "mean_neg_mass": mean_neg,
                    "n_draws": int(stats.count),
                    "g19_bar": bar,
                    "message": msg,
                })
            else:
                raise RuntimeError(msg)


# --------------------------------------------------------------------------- #
# born_sample_round — sequential conditional sampling + selective update       #
# --------------------------------------------------------------------------- #
def _stab_paulis(stab) -> dict:
    """Accept a parsed stabilizer object (``.paulis``) or a plain paulis dict."""
    if hasattr(stab, "paulis"):
        return dict(stab.paulis)
    return dict(stab)


def _path_bonds(state, paulis: dict) -> list[str]:
    """The bond index names along the layout's plaquette path through the support —
    the bonds :func:`dynamics.apply_stab_branch` grows and the ones NTU truncates."""
    path = state.layout.plaquette_path({int(k): str(v) for k, v in paulis.items()})
    bonds: list[str] = []
    for a, b in zip(path[:-1], path[1:]):
        ta = _site_tensor(state, a)
        tb = _site_tensor(state, b)
        shared = set(ta.inds) & set(tb.inds)
        if not shared:
            raise RuntimeError(f"no bond between path-adjacent sites Q{a} and Q{b}")
        bonds.extend(sorted(shared))
    return bonds


def born_sample_round(state, stabs: list, b: float, arm: str, rng, R_n: int, R_x: int,
                      D_cap: int, *, g19_bar: float | None = None,
                      stats: C3Stats | None = None,
                      log_only: bool = False) -> list[int]:
    """One round of sequential conditional Born sampling over ``stabs`` (contract §3):
    per stabilizer, ``q = Tr(E_s rho) / Tr(rho)`` through the PRODUCTION site-cap path,
    sample the bit, apply the SELECTIVE ``sqrt(E_s)`` branch via
    ``dynamics.apply_stab_branch`` (+ ``dynamics.ntu_truncate`` on the grown support-path
    bonds), renormalize with a ledger entry, and run the negativity witness on EVERY
    Born draw. Emits the RAW ``s`` bits (detector folding is :func:`s_to_det`,
    downstream — the ``seam.py`` convention).

    Boundary dims: ``R_n`` = the norm-pass dim (``Tr(rho)``), ``R_x`` = the sample-pass
    dim (the ``E_s`` expectation) — the G1.1 chi_b sub-gate arms set them equal per arm.
    The cache is REBUILT per stabilizer (the state mutates after every selective
    update; a stale cache is a correctness bug, not an optimization).

    Witness call convention (documented design decision): the two branch weights obey
    ``q_0 + q_1 = Tr(rho)``, so with a positive trace at most ONE of them can be
    negative; the witness is called once per draw on ``min(q_0, q_1)``, which carries
    the draw's entire negative mass and dominates rule (i) for both branches.
    ``g19_bar`` defaults to the registered Weyl floor ``4.8e-4`` until the measured
    G1.9-pre bar is wired in by the run scripts. ``stats`` is the run-level
    :class:`C3Stats` accumulator (C3 rule ii; the run driver owns it) and ``log_only``
    the v4.2 C3 arm-scoping flag (R=4 exerciser arm: would-trips logged as
    ``c3_would_trip``, never raised) — both passed through to
    :func:`negativity_witness` on every draw.
    """
    from . import dynamics  # lazy: parallel-build + import-order safety

    bar = float(g19_bar) if g19_bar is not None else G19_BAR_WEYL_FLOOR
    if stats is None:
        # C3 rule (ii) is RUN-level (contract §4, non-optional): with no run
        # accumulator passed it is NOT enforced in this call — mark that fact so a
        # stats-less run is ledger-detectable (per-draw born_negativity entries
        # still carry the audit data for an offline mean).
        state.ledger.append({
            "kind": "c3_rule_ii_inactive",
            "where": "born_sample_round",
            "g19_bar": bar,
        })
    bits: list[int] = []
    for j, stab in enumerate(stabs):
        paulis = _stab_paulis(stab)

        cache_n = norm_cache(state, int(R_n))
        tr = expect_site_caps(state, {}, cache=cache_n, R_n=int(R_n)).real
        cache_x = cache_n if int(R_x) == int(R_n) else norm_cache(state, int(R_x))
        q1_raw = stab_expectation(state, paulis, 1, b, arm, cache=cache_x, R_n=int(R_x))
        q0_raw = tr - q1_raw

        negativity_witness(min(q0_raw, q1_raw), tr, state.ledger, bar,
                           stats=stats, log_only=log_only)
        if tr <= NUMERICAL_ZERO:
            raise RuntimeError(
                f"C3_STOP: nonpositive parent trace {tr:.6e} at stab {j} (state collapsed)")

        p1 = min(1.0, max(0.0, q1_raw / tr))
        outcome = 1 if float(rng.random()) < p1 else 0
        bits.append(outcome)

        # SELECTIVE sqrt(E_s) branch (dynamics owns the TT + NTU internals)
        stab_tt = dynamics.stab_channel_tt(paulis, outcome, float(b), str(arm),
                                           state.layout, state.device)
        dynamics.apply_stab_branch(state, stab_tt)
        # v4.3 TWO-PASS truncation (2026-07-10 first-execution fix): pass 1 bounds
        # every grown path bond to 4*D_cap by a local SVD gauge cut so the NTU
        # metric cluster (pass 2) never doubles a raw 25*D neighbor bond — a
        # (25D)^4 transfer object is byte-infeasible at D=16 (dynamics.svd_precut_bond).
        path_bonds = _path_bonds(state, paulis)
        for bond in path_bonds:
            if state.tn.ind_size(bond) > 4 * int(D_cap):
                dynamics.svd_precut_bond(state, bond, 4 * int(D_cap))
        for bond in path_bonds:
            if state.tn.ind_size(bond) > int(D_cap):
                dynamics.ntu_truncate(state, bond, int(D_cap))

        # renormalize + ledger (engine convention; the pre-renorm trace is the record)
        tr_new = pepo_trace(state).real
        if tr_new <= NUMERICAL_ZERO:
            raise RuntimeError(
                f"C3_STOP: nonpositive post-branch trace {tr_new:.6e} at stab {j} "
                f"(outcome {outcome})")
        state.tn.multiply_(1.0 / tr_new)
        state.ledger.append({
            "kind": "renorm",
            "stab": j,
            "outcome": int(outcome),
            "trace_raw": float(tr_new),
            "p1": float(p1),
            "q1_raw": float(q1_raw),
            "q0_raw": float(q0_raw),
            # contract §3: measured TT ranks logged (re-review 2026-07-10)
            "tt_ranks": tuple(int(r) for r in stab_tt.ranks),
        })
    return bits


# --------------------------------------------------------------------------- #
# terminal_readout_obs — the pinned obs law VERBATIM (contract §3, v4 pin)     #
# --------------------------------------------------------------------------- #
def _terminal_site_effects(logical: dict, isx: dict, b: float, device) -> dict:
    """The pinned per-site terminal-readout effect pairs, ``{q: (E0_q, E1_q)}`` over
    the SORTED logical support (contract §3, v4 formula pin):

      * ``F1 = |1><1| + b |2><2|``, ``F0 = |0><0| + (1-b) |2><2|`` (``F0 + F1 = I``;
        ``F0 - F1 = diag(1, -1, 1-2b)``, consistent with F2);
      * each X-flagged site (``isx[q]`` truthy) H-CONJUGATED: ``E_c = H F_c H``.

    This is the ONE shared effect-construction path (v4.2 EXACT-PROBABILITY SEAM):
    both the sampling path (:func:`terminal_readout_obs`) and the exact-probability
    seam (:func:`terminal_readout_obs_prob`) compose THROUGH this helper, so an
    engine-side killer (e.g. the G1.1 b-swap) exercises the engine's own effects.
    """
    bval = float(b)
    if not 0.0 <= bval <= 1.0:
        raise ValueError(f"readout bias b must be in [0, 1] (got {bval})")
    f1 = torch.zeros((3, 3), dtype=CDTYPE, device=device)
    f1[1, 1] = 1.0
    f1[2, 2] = bval
    f0 = torch.zeros((3, 3), dtype=CDTYPE, device=device)
    f0[0, 0] = 1.0
    f0[2, 2] = 1.0 - bval
    h = _qutrit_hadamard(device)

    support = sorted(int(q) for q in logical)
    if not support:
        raise ValueError("terminal readout: empty logical support")

    effects: dict[int, tuple[torch.Tensor, torch.Tensor]] = {}
    for q in support:
        if isx.get(q, 0):
            effects[q] = (h @ f0 @ h, h @ f1 @ h)
        else:
            effects[q] = (f0, f1)
    return effects


def terminal_readout_obs(state, logical: dict, isx: dict, b: float, m: int, rng, *,
                         g19_bar: float | None = None,
                         stats: C3Stats | None = None,
                         log_only: bool = False) -> int:
    """The pinned terminal-readout obs law (contract §3, BOTH-sides pin — v2 B3 + v3
    support/basis + v4 formula fixes):

      * parity over the LOGICAL SUPPORT ONLY (``logical`` — the ``sched.logical`` dict,
        weight-3 at d3; NEVER all data sites);
      * each X-flagged logical site (``isx[q]`` truthy — the ``sv_sampler``
        ``log_supp_isx`` "the logical readout keeps its OWN X-rotation" convention) is
        H-CONJUGATED before the diagonal POVM;
      * per-site effects BY FORMULA via the shared :func:`_terminal_site_effects`
        helper: ``F1 = |1><1| + b |2><2|``, ``F0 = |0><0| + (1-b) |2><2|``
        (``F0 + F1 = I``; ``F0 - F1 = diag(1, -1, 1-2b)``, consistent with F2);
      * obs = ``parity(bits) XOR m``.

    Sampling is sequential-conditional over the support through the site-cap path: the
    already-sampled sites stay capped with their realized effects, so the emitted bit
    tuple is drawn from the exact JOINT distribution ``Tr(rho * prod_q F_{c_q})``.
    The state is NOT mutated (terminal round: no post-measurement state is consumed —
    the referee's biased-b obs composition is the A4-side mirror of exactly this law).
    Each per-site draw runs the negativity witness (a terminal draw is a Born draw of
    the run; C3 rule ii is per-draw): ``g19_bar`` is resolved ONCE like
    :func:`born_sample_round` does (the measured G1.9 bar when wired by the run
    scripts, else the registered Weyl floor) and passed to every witness call, along
    with the run-level ``stats`` accumulator and the v4.2 ``log_only`` arm-scoping
    flag.
    """
    device = torch.device(state.device)
    bar = float(g19_bar) if g19_bar is not None else G19_BAR_WEYL_FLOOR
    if stats is None:
        # C3 rule (ii) unenforced without the run accumulator — ledger-mark it
        # (same convention as born_sample_round; re-review 2026-07-10).
        state.ledger.append({
            "kind": "c3_rule_ii_inactive",
            "where": "terminal_readout_obs",
            "g19_bar": bar,
        })
    effects = _terminal_site_effects(logical, isx, b, device)

    caps_acc: dict[int, torch.Tensor] = {}
    parity = 0
    for q, (e0, e1) in effects.items():
        den = expect_site_caps(state, caps_acc).real
        num1 = expect_site_caps(state, {**caps_acc, q: e1}).real
        negativity_witness(min(num1, den - num1), den, state.ledger, bar,
                           stats=stats, log_only=log_only)
        if den <= NUMERICAL_ZERO:
            raise RuntimeError(
                f"C3_STOP: nonpositive conditional trace {den:.6e} in terminal readout "
                f"at site {q}")
        p1 = min(1.0, max(0.0, num1 / den))
        bit = 1 if float(rng.random()) < p1 else 0
        caps_acc[q] = e1 if bit else e0
        parity ^= bit
    return int(parity ^ (int(m) & 1))


def terminal_readout_obs_prob(state, logical: dict, isx: dict, b: float, m: int) -> float:
    """EXACT ``P(obs = 1)`` for the pinned terminal-readout obs law — the ENGINE-SIDE
    killer seam (contract §3, v4.2 EXACT-PROBABILITY SEAM: the Stage-4 vacuity lens
    proved the G1.1 b-swap killer never invoked the engine, comparing the test's own
    referee to itself; this function exists so the killer asserts ENGINE-side —
    engine == unswapped dense composition at 1e-10 AND engine != swapped dense).

    The probability is composed through the SAME per-site effect-construction code the
    sampling path uses (:func:`_terminal_site_effects` — one construction, two
    consumers): enumerate the 2^w outcome tuples over the sorted logical support, sum
    the exact joint weights ``Tr(rho * prod_q E_{c_q})`` (exact contraction route, no
    boundary-MPS cache) over the tuples whose parity XOR ``m`` equals 1, and normalize
    by ``Tr(rho)``. The value is returned UNCLAMPED (a negative or >1 composition is
    exactly the discrepancy the seam must expose, never mask). The state is NOT
    mutated; no Born draw occurs (no witness call — this is a deterministic read).
    """
    device = torch.device(state.device)
    effects = _terminal_site_effects(logical, isx, b, device)
    support = list(effects)
    n = len(support)

    tr = expect_site_caps(state, {}).real
    if tr <= NUMERICAL_ZERO:
        raise RuntimeError(
            f"C3_STOP: nonpositive trace {tr:.6e} in terminal_readout_obs_prob")

    target = 1 ^ (int(m) & 1)  # parity value that makes obs = parity XOR m equal 1
    total = 0.0
    for mask in range(1 << n):
        parity = bin(mask).count("1") & 1
        if parity != target:
            continue
        caps = {q: effects[q][(mask >> i) & 1] for i, q in enumerate(support)}
        total += expect_site_caps(state, caps).real
    return float(total / tr)


# --------------------------------------------------------------------------- #
# s <-> det — the seam.py detector conventions (contract §3 G1.1 pin)          #
# --------------------------------------------------------------------------- #
def s_to_det(s_bits, R: int, n_stab: int) -> np.ndarray:
    """RAW per-round syndrome bits -> detector bits, the ``seam.py`` convention
    (``teacher_shots_to_events`` / ``bayes_floor``, identical fold):

        ``det(0, j) = s(0, j)``;  ``det(r, j) = s(r, j) XOR s(r-1, j)`` for ``r >= 1``.

    ``s_bits`` is array-like with last axis of length ``R * n_stab``, ROUND-MAJOR then
    stab-order (the kernel packing layout). Returns ``uint8`` with the same shape.
    """
    R, n_stab = int(R), int(n_stab)
    s = np.asarray(s_bits, dtype=np.uint8)
    if s.shape[-1] != R * n_stab:
        raise ValueError(
            f"s_bits last axis {s.shape[-1]} != R*n_stab = {R * n_stab}")
    shp = s.shape
    sr = s.reshape(shp[:-1] + (R, n_stab))
    det = np.empty_like(sr)
    det[..., 0, :] = sr[..., 0, :]
    if R > 1:
        det[..., 1:, :] = sr[..., 1:, :] ^ sr[..., :-1, :]
    return det.reshape(shp)


def det_to_s(det_bits, R: int, n_stab: int) -> np.ndarray:
    """Detector bits -> RAW per-round syndrome bits — the pinned G1.1 inversion
    (contract §3: ``s(r, j) = XOR_{r' <= r} det(r', j)``, applied before the
    ``reevolve_onto_records`` referee call). Exact inverse of :func:`s_to_det`;
    same layout/shape conventions. Returns ``uint8``.
    """
    R, n_stab = int(R), int(n_stab)
    det = np.asarray(det_bits, dtype=np.uint8)
    if det.shape[-1] != R * n_stab:
        raise ValueError(
            f"det_bits last axis {det.shape[-1]} != R*n_stab = {R * n_stab}")
    shp = det.shape
    dr = det.reshape(shp[:-1] + (R, n_stab))
    # cumulative XOR over the round axis (== parity of the running sum mod 2)
    s = np.bitwise_xor.accumulate(dr, axis=-2)
    return s.astype(np.uint8).reshape(shp)

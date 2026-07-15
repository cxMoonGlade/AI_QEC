from __future__ import annotations

r"""Single-wire stabilizer tensor train for the unsquared ``sqrt(e)`` diagonal.

  * the single-wire object is the UNSQUARED diagonal ``v = sqrt(e)`` over
    ``(3,)*w`` — the parent ``dynamics._fused_stab_diag`` builds the ket⊗bra
    square ``v v^T``; that squaring is exactly what this module removes;
  * the per-site diagonal is ``e_i = 1/2 (1 + (-1)^s prod_q
    d_q)`` with ``d_q = +1 (t=0), -1 (t=1), d2 (t=2)``, ``d2`` the arm table
    (A/C: ``1-2b``; B1: ``+1``; B2: ``-1``) — identical in the parent dynamics,
    in the bounded reference implementations;
  * TT rank bound = ``2 min(w_L, w_R) + 1`` per cut — **(3, 5, 3)** for w=4,
    **(3,)** for w=2 (the doubled-wire bound is its square).
    The bound is always asserted as ``<=``; measured ranks are carried on the
    returned object for callers to inspect.

``_tt_svd`` is local with the physical dimension parameterized; ``_insert_core``
and the ``fuse_multibonds``
skeleton are leg-dimension-agnostic and IMPORTED from the parent. The H sandwich
uses the local gate formula. X supports are H-rotated
outside the TT (leaked levels are H-inert, so the leaked rows are
basis-independent).
"""

from dataclasses import dataclass, field

import torch
import quimb.tensor as qtn

from ...numerics import NUMERICAL_ZERO
from ..pepo.dynamics import _assert_path_adjacent, _insert_core
from .state import CDTYPE, QUTRIT, RDTYPE, apply_site_op, phys_name, qutrit_gate, site_tensor


@dataclass
class SingleWireStabTT:
    """The exact numeric tensor train of one stabilizer branch's SINGLE-WIRE
    diagonal ``sqrt(e)`` along the plaquette path.

    ``path``    ordered grid-adjacent engine positions through the support;
    ``cores``   ``w`` TT cores, core ``p`` of shape ``(r_{p-1}, 3, r_p)`` with
                boundary ranks ``r_0 = r_w = 1`` stored explicitly (squeezed at
                application time);
    ``x_sites`` support sites with Pauli ``X`` — the 1-site H sandwich applied
                outside the TT;
    ``outcome`` the syndrome bit ``s`` in {0, 1}; single-wire evolution is
                selective because a pure state cannot carry a branch sum;
    ``ranks``   the measured TT bond ranks ledgered by callers.
    """

    path: tuple
    cores: list = field(default_factory=list)
    x_sites: tuple = ()
    outcome: int = 0
    b: float = 0.0
    arm: str = "A"
    ranks: tuple = ()


def leaked_weight(b: float, arm: str) -> float:
    """The per-site leaked parity weight ``d_q(leaked)``:
    arm A/C -> ``1 - 2b``; B1 -> ``+1``; B2 -> ``-1``.
    Arm C's weight remains defined for the shared physical table even though
    trajectory execution currently accepts arm A only."""
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


def _stab_sqrt_diag(w: int, outcome: int, b: float, arm: str, device) -> torch.Tensor:
    """The SINGLE-WIRE diagonal ``v = sqrt(e)`` over ``(3,)*w``, axes in PATH
    order: ``e_i = 1/2 (1 + (-1)^s prod_q d_q)`` with
    ``d_q = (+1, -1, d2)``. No ket⊗bra product is formed.
    Every site is read as a Z parity here; X supports are H-rotated OUTSIDE."""
    d2 = leaked_weight(b, arm)
    dvec = torch.tensor([1.0, -1.0, d2], dtype=RDTYPE, device=device)
    prod = dvec
    for _ in range(int(w) - 1):
        prod = prod[..., None] * dvec  # axes accumulate in path order
    sign = 1.0 if (int(outcome) & 1) == 0 else -1.0
    e = 0.5 * (1.0 + sign * prod)  # (3,)*w
    return torch.sqrt(torch.clamp(e, min=0.0)).to(CDTYPE)


def _tt_svd(diag: torch.Tensor, local_dim: int):
    """EXACT TT decomposition of a ``(local_dim,)*w`` diagonal by sequential SVD;
    candidate values with ``sigma <= 1e-12 * sigma_1`` (per-SVD) dropped — the
    parent ``dynamics._tt_svd`` with the literal local dimension 9 parametrized
    to 3. Returns ``(cores, ranks)`` with core ``p`` of shape
    ``(r_{p-1}, local_dim, r_p)``."""
    D = int(local_dim)
    w = diag.dim()
    cores = []
    ranks = []
    m = diag.reshape(D, -1)
    rl = 1
    for _ in range(w - 1):
        U, S, Vh = torch.linalg.svd(m, full_matrices=False)
        if float(S[0]) <= 0.0:
            r = 1
        else:
            r = max(1, int((S > NUMERICAL_ZERO * S[0]).sum()))
        cores.append(U[:, :r].reshape(rl, D, r).contiguous())
        ranks.append(r)
        m = (S[:r, None].to(CDTYPE) * Vh[:r]).reshape(r * D, -1)
        rl = r
    cores.append(m.reshape(rl, D, 1).contiguous())
    return cores, tuple(ranks)


def tt_rank_bounds(w: int) -> tuple:
    """The derived single-wire per-bond TT rank bound ``2 min(w_L, w_R) + 1``.
    It follows from distinct left-product values of ``w_L`` factors in {+1, -1, c} at
    generic ``c`` — the parent derivation's square root): (3, 5, 3) for w=4,
    (3,) for w=2. Class (a) bound; asserted as ``<=`` ALWAYS."""
    return tuple(2 * min(p, int(w) - p) + 1 for p in range(1, int(w)))


def stab_tt_singlewire(paulis: dict, outcome: int, b: float, arm: str, layout,
                       device: str) -> SingleWireStabTT:
    """The exact numeric TT of the single-wire ``sqrt(E_s)`` diagonal over the
    support.

    Builds the ``3^w`` diagonal ``e_i`` from the parity formula, takes the square
    root without forming a ket⊗bra product, and TT-decomposes it exactly
    (SVD; ``sigma <= 1e-12 sigma_1`` dropped) along ``layout.plaquette_path``.

    Measured TT bond ranks must be no greater than the derived single-wire bound
    ``2 min(w_L, w_R) + 1`` at each cut. Measured ranks are carried on the
    returned object so callers can ledger them.

    X supports are NOT folded into the TT: they are recorded on ``x_sites`` and
    sandwiched with one-site H gates by :func:`apply_stab_branch`; leaked levels
    are H-inert.
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

    diag = _stab_sqrt_diag(w, outcome, b, arm, dev)
    cores, ranks = _tt_svd(diag, QUTRIT)
    bounds = tt_rank_bounds(w)
    assert all(r <= bd for r, bd in zip(ranks, bounds)), (
        f"single-wire stab TT rank above the derived bound (arm={arm}, b={b}, w={w}): "
        f"measured {ranks}, bound {bounds} (2 min(w_L, w_R) + 1)")
    x_sites = tuple(sorted(int(s) for s, pp in paulis.items() if str(pp).upper() == "X"))
    return SingleWireStabTT(path=path, cores=cores, x_sites=x_sites,
                            outcome=int(outcome), b=float(b), arm=str(arm).upper(),
                            ranks=ranks)


def apply_stab_branch(state, stab_tt: SingleWireStabTT) -> None:
    """Apply one selective ``sqrt(E_s)`` branch to the state: one-site H
    sandwich on the X supports outside the TT,
    TT cores multiplied onto the dim-3 physical legs along the support path
    (fresh-uuid TT bonds), TT bonds fused with the pre-existing grid bonds via
    ``fuse_multibonds`` using the leg-dimension-agnostic parent skeleton.

    GROWS the support-path bonds by the TT ranks; NO truncation inside (the
    caller applies its truncation policy). The result is the unnormalized
    ``sqrt(E_s) |psi>`` — the caller renormalizes after truncation.
    Arm-C dephase is intentionally absent: this trajectory supports arm A only,
    and
    a pure state has no cross-sector coherence channel to dephase selectively).
    """
    dev = site_tensor(state, stab_tt.path[0]).data.device
    h = qutrit_gate("H", dev)
    for pos in stab_tt.x_sites:
        apply_site_op(state, pos, h)

    w = len(stab_tt.path)
    tt_bonds = [qtn.rand_uuid() for _ in range(w - 1)]
    for p, pos in enumerate(stab_tt.path):
        t = site_tensor(state, pos)
        lname = tt_bonds[p - 1] if p > 0 else None
        rname = tt_bonds[p] if p < w - 1 else None
        _insert_core(t, phys_name(pos), stab_tt.cores[p].to(device=dev), lname, rname)
    # fuse each new TT bond with the pre-existing grid bond of the same edge
    # (a path edge with no pre-existing bond simply keeps the TT bond).
    state.tn.fuse_multibonds(inplace=True)

    for pos in stab_tt.x_sites:
        apply_site_op(state, pos, h)

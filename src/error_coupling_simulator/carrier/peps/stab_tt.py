from __future__ import annotations

r"""Single-wire stabilizer TT — the UNSQUARED ``sqrt(e)`` diagonal (RUNG-B spike).

Binding doc: ``docs/nonpauli_teacher/peps_singlewire_spike_contract.md`` §2/§3
(rows ``stab_tt_singlewire`` / ``apply_stab_branch``), grounded on SF3/SF4:

  * the single-wire object is the UNSQUARED diagonal ``v = sqrt(e)`` over
    ``(3,)*w`` — the parent ``dynamics._fused_stab_diag`` builds the ket⊗bra
    square ``v v^T``; that squaring is exactly what this module removes (SF3);
  * the per-site diagonal is the SHARED F2 form ``e_i = 1/2 (1 + (-1)^s prod_q
    d_q)`` with ``d_q = +1 (t=0), -1 (t=1), d2 (t=2)``, ``d2`` the arm table
    (A/C: ``1-2b``; B1: ``+1``; B2: ``-1``) — identical in the parent dynamics,
    in ``mps_forward._apply_sqrt_Es``/``_arm_d2``, and in the referee (SF4);
  * TT rank bound = ``2 min(w_L, w_R) + 1`` per cut — **(3, 5, 3)** for w=4,
    **(3,)** for w=2 (SF3, class (a) bound; the parent bound is its square).
    Asserted as ``<=`` ALWAYS; measured ranks are carried on the returned object
    for ledgering (WP3 equality at arm A, b=0.9 is the SW3 gate's read, not an
    engine assert — a below-bound measurement there is a porting bug, SF3).

Ported vs imported (D4): ``_tt_svd`` is PORTED with the local dim parametrized
(the parent has a literal 9 — SF3); ``_insert_core`` and the ``fuse_multibonds``
skeleton are leg-dimension-agnostic and IMPORTED from the parent. The H sandwich
uses the LOCAL gate formula (referee independence, D4). X supports are H-rotated
OUTSIDE the TT (F2 — leaked levels are H-inert, so the leaked rows are
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
    diagonal ``sqrt(e)`` along the plaquette path (contract §2/§3).

    ``path``    ordered grid-adjacent engine positions through the support;
    ``cores``   ``w`` TT cores, core ``p`` of shape ``(r_{p-1}, 3, r_p)`` with
                boundary ranks ``r_0 = r_w = 1`` stored explicitly (squeezed at
                application time);
    ``x_sites`` support sites with Pauli ``X`` — the 1-site H sandwich applied
                OUTSIDE the TT (F2);
    ``outcome`` the syndrome bit ``s`` in {0, 1} (single-wire is always
                SELECTIVE — a pure state cannot carry a branch sum, SF6);
    ``ranks``   the MEASURED TT bond ranks (ledgered by the callers; WP3).
    """

    path: tuple
    cores: list = field(default_factory=list)
    x_sites: tuple = ()
    outcome: int = 0
    b: float = 0.0
    arm: str = "A"
    ranks: tuple = ()


def leaked_weight(b: float, arm: str) -> float:
    """The per-site LEAKED parity weight ``d_q(leaked)`` (SF4, the normative
    F2 b/arm table): arm A/C -> ``1 - 2b``; B1 -> ``+1``; B2 -> ``-1``.
    LOCAL formula (referee independence, D4). Arm C's weight is defined here for
    the shared table; the trajectory arm fence (SW-S2) lives in trajectory.py."""
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
    order: ``e_i = 1/2 (1 + (-1)^s prod_q d_q)`` with ``d_q = (+1, -1, d2)`` —
    the F2 formula VERBATIM, UNSQUARED (SF3: no ket⊗bra product is formed).
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
    parent ``dynamics._tt_svd`` PORTED with the literal local dim 9 parametrized
    to 3 (SF3/D4). Returns ``(cores, ranks)`` with core ``p`` of shape
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
    """The DERIVED single-wire per-bond TT rank bound ``2 min(w_L, w_R) + 1``
    (SF3: distinct left-product values of ``w_L`` factors from {+1, -1, c} at
    generic ``c`` — the parent derivation's square root): (3, 5, 3) for w=4,
    (3,) for w=2. Class (a) bound; asserted as ``<=`` ALWAYS."""
    return tuple(2 * min(p, int(w) - p) + 1 for p in range(1, int(w)))


def stab_tt_singlewire(paulis: dict, outcome: int, b: float, arm: str, layout,
                       device: str) -> SingleWireStabTT:
    """The EXACT numeric TT of the single-wire ``sqrt(E_s)`` diagonal over the
    support (contract §3 row ``stab_tt_singlewire``).

    Builds the ``3^w`` diagonal ``e_i`` from the F2 formula, takes the square
    root (UNSQUARED — no ket⊗bra product, SF3), and TT-decomposes it EXACTLY
    (SVD; ``sigma <= 1e-12 sigma_1`` dropped) along ``layout.plaquette_path``.

    RANK ASSERT (contract §2/§3): measured TT bond ranks ``<=`` the derived
    single-wire bound ``2 min(w_L, w_R) + 1`` at each cut — ALWAYS ``<=``, never
    ``==`` (the WP3 equality at arm A, b=0.9 is the SW3 GATE's read; measured
    ranks are carried on the returned object so callers ledger them).

    X supports are NOT folded into the TT: they are recorded on ``x_sites`` and
    sandwiched with 1-site H gates by :func:`apply_stab_branch` (F2 — H-rotation
    outside the TT; leaked levels H-inert).
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
        f"measured {ranks}, bound {bounds} (SF3: 2 min(w_L, w_R) + 1 — class (a))")
    x_sites = tuple(sorted(int(s) for s, pp in paulis.items() if str(pp).upper() == "X"))
    return SingleWireStabTT(path=path, cores=cores, x_sites=x_sites,
                            outcome=int(outcome), b=float(b), arm=str(arm).upper(),
                            ranks=ranks)


def apply_stab_branch(state, stab_tt: SingleWireStabTT) -> None:
    """Apply one SELECTIVE ``sqrt(E_s)`` branch to the state (contract §2 op
    table): 1-site H sandwich on the X supports (OUTSIDE the TT, local formula),
    TT cores multiplied onto the dim-3 physical legs along the support path
    (fresh-uuid TT bonds), TT bonds fused with the pre-existing grid bonds via
    ``fuse_multibonds`` — the parent skeleton, leg-dimension-agnostic (SF3).

    GROWS the support-path bonds by the TT ranks; NO truncation inside (the
    caller truncates under the §6.1 policy). The result is the UNNORMALIZED
    ``sqrt(E_s) |psi>`` — the caller renormalizes after truncation.
    Arm-C dephase is intentionally ABSENT (SW-S2: arm C fenced out of the spike;
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

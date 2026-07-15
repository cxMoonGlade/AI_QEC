from __future__ import annotations

r"""Single-wire qutrit PEPS state and codestate builder.

Geometry and ket-layer chain machinery are reused from the retained PEPO carrier:
``PepoLayout``, ``_apply_chain_operator``, ``_ket_norm_sq``, ``_fuse_pair``, and
``_site_tensors_by_pos``.

Single-wire finalization keeps the ket layer only — the ket⊗bra
fuse (parent step 4) never happens. The physical leg stays dim **3** (named
``k{pos}``), ket bonds are renamed to the grid-edge names ``B{p}_{q}``, untouched grid
edges are materialized as dim-1 bonds, and the unit-NORM constant is
``tr_m**(-1/(2n))`` per site (the parent's ``tr_m**(-1/n)`` is
density-matrix-specific).

For reference independence, this package shares no code path
with ``carrier/exact/qutrit_dm`` — the qutrit gate table below (H/X/Y/Z/S/S_DAG on
the computational ``{|0>,|1>}`` block, leaked ``|2>`` inert) is built locally BY
FORMULA, mirroring the ``mps_forward._qutrit_gate`` values; the parent
layout's one reference import (``qudit_hadamard`` for the seed) is replaced by the
local formula here.

GPU-only, torch-cuda-complex128; devices are passed in, never guessed.
"""

import torch

from ...numerics import NUMERICAL_ZERO
from ..pepo.layout import (
    PepoLayout,
    _apply_chain_operator,
    _fuse_pair,
    _ket_bond_name,
    _ket_norm_sq,
    _site_tensors_by_pos,
    fused_bond_name,
    site_tag,
)

CDTYPE = torch.complex128
RDTYPE = torch.float64

#: Qutrit local dimension: the single-wire physical leg is dim 3, not 9.
QUTRIT = 3


# --------------------------------------------------------------------------- #
# Local single-qutrit gate table                                               #
# --------------------------------------------------------------------------- #
def qutrit_gate(name: str, device, dtype=CDTYPE) -> torch.Tensor:
    """A single-qutrit FRAME gate ``(3,3)`` on the computational ``{0,1}`` block,
    ``|2>`` inert. The table mirrors ``mps_forward._qutrit_gate`` but is built
    locally by formula, so the engine shares no code path with the reference."""
    nm = str(name).upper()
    m = torch.zeros((QUTRIT, QUTRIT), dtype=dtype, device=device)
    if nm == "I":
        return torch.eye(QUTRIT, dtype=dtype, device=device)
    if nm == "H":
        inv2 = 1.0 / (2.0 ** 0.5)
        m[0, 0] = inv2
        m[0, 1] = inv2
        m[1, 0] = inv2
        m[1, 1] = -inv2
        m[2, 2] = 1.0
        return m
    if nm == "X":
        m[0, 1] = 1.0
        m[1, 0] = 1.0
        m[2, 2] = 1.0
        return m
    if nm == "Y":
        m[0, 1] = -1.0j
        m[1, 0] = 1.0j
        m[2, 2] = 1.0
        return m
    if nm == "Z":
        m[0, 0] = 1.0
        m[1, 1] = -1.0
        m[2, 2] = 1.0
        return m
    if nm == "S":
        m[0, 0] = 1.0
        m[1, 1] = 1.0j
        m[2, 2] = 1.0
        return m
    if nm == "S_DAG":
        m[0, 0] = 1.0
        m[1, 1] = -1.0j
        m[2, 2] = 1.0
        return m
    raise ValueError(f"unsupported single-qutrit gate {name!r}")


def phys_name(pos: int) -> str:
    """The dim-3 physical index name ``k{pos}`` at engine position ``pos``."""
    return f"k{int(pos)}"


# --------------------------------------------------------------------------- #
# State object                                                                 #
# --------------------------------------------------------------------------- #
class PepsState:
    """The single-wire pure-state qutrit PEPS.

    Attributes: ``tn`` (quimb ``TensorNetwork``; one rank<=5 site tensor per data
    qutrit, tagged ``Q{pos}``, physical index ``k{pos}`` of dim **3**, virtual
    bonds ``B{p}_{q}`` on the grid edges), ``layout`` (:class:`PepoLayout`),
    ``device`` (str), ``ledger`` (list of dicts in the
    pepo convention: discarded weight on the SQUARED-sigma RELATIVE scale, norm
    shifts logged). NO global gauge/canonical form is tracked. Positivity is
    structural for a pure state, so density-matrix negativity machinery is
    intentionally absent; per-read accuracy instruments and the norm ledger
    provide the applicable numerical diagnostics.

    Construction asserts torch complex128 tensors on a CUDA device,
    rank <= 5, one tensor per position with the dim-3 physical leg.
    """

    def __init__(self, tn, layout: PepoLayout, device: str, ledger: list | None = None) -> None:
        self.tn = tn
        self.layout = layout
        self.device = str(device)
        self.ledger = [] if ledger is None else ledger

        dev = torch.device(self.device)
        if dev.type != "cuda":
            raise ValueError(
                f"PepsState tensors must be torch CUDA complex128; "
                f"got device {self.device!r}")
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
            k = phys_name(pos)
            if k not in t.inds:
                raise ValueError(f"site {pos}: physical index {k!r} missing")
            if int(data.shape[t.inds.index(k)]) != QUTRIT:
                raise ValueError(
                    f"site {pos}: physical index {k!r} is not dim 3 (single-wire)")

    def copy(self) -> "PepsState":
        """Deep-copy the tensor network; the ledger is copied SHALLOW-list so the
        copy's entries do not append into the source (probe/trajectory isolation)."""
        return PepsState(tn=self.tn.copy(), layout=self.layout, device=self.device,
                         ledger=list(self.ledger))


def site_tensor(state: PepsState, pos: int):
    """The unique site tensor tagged ``Q{pos}``."""
    ts = state.tn.select_tensors(f"Q{int(pos)}", which="all")
    if len(ts) != 1:
        raise RuntimeError(f"expected exactly one tensor tagged Q{pos}, found {len(ts)}")
    return ts[0]


def apply_site_op(state: PepsState, pos: int, op: torch.Tensor) -> None:
    """Contract a ``(3,3)`` operator onto the physical leg ``k{pos}``.

    Single-site by construction: bond dimensions are asserted unchanged because
    one-site gates and Kraus branches are bond-inert on a PEPS. The op is
    NOT required to be unitary (sqrt-effect collapses and forced Kraus branches
    ride this same path, unnormalized).
    """
    if op.shape != (QUTRIT, QUTRIT):
        raise ValueError(f"site op must be (3, 3), got {tuple(op.shape)}")
    t = site_tensor(state, pos)
    kname = phys_name(pos)
    ax = t.inds.index(kname)
    shape_before = tuple(t.data.shape)
    data = torch.movedim(torch.tensordot(op, t.data, dims=([1], [ax])), 0, ax)
    assert tuple(data.shape) == shape_before, (
        f"single-site op changed the tensor shape at Q{pos}: "
        f"{shape_before} -> {tuple(data.shape)}")
    t.modify(data=data.contiguous())


def renormalize(state: PepsState, norm_sq: float) -> None:
    """Scale the state to unit norm given a measured ``<psi|psi>`` (the caller's
    read — exact or boundary route; the pre-scale value is the caller's ledger
    record). Raises on a collapsed (nonpositive) norm."""
    ns = float(norm_sq)
    if not ns > NUMERICAL_ZERO:
        raise RuntimeError(f"renormalize: nonpositive norm {ns:.6e} (state collapsed)")
    state.tn.multiply_(1.0 / (ns ** 0.5))


# --------------------------------------------------------------------------- #
# Codestate builder and single-wire finalization                              #
# --------------------------------------------------------------------------- #
def build_codestate_peps(sched, m: int, device: str = "cuda") -> PepsState:
    """Build the codestate ``|m>_L`` as a single-wire :class:`PepsState`.

    The builder reuses the parent's ket layer: H-spread seed
    ``(1,1,0)/sqrt(2)``; per check one bond-2
    W-tensor chain ``(I + c.g)/2`` along ``plaquette_path`` in ``sched.stabilizers``
    order, then the logical-sector projector — the oracle's order; nonzero-norm
    ASSERTED for BOTH m sectors), with two single-wire changes:

      * the seed ``H|0>`` comes from the LOCAL gate formula (:func:`qutrit_gate`),
        never the reference's ``qudit_hadamard`` (the one parent reference import
        is replaced here);
      * NO ket⊗bra fuse (parent step 4): the physical leg stays dim 3, and the
        unit-NORM constant is ``tr_m**(-1/(2n))`` per site.

    Structural guarantees carried on the result: the ``k=2`` slice
    of every site tensor is exactly 0.0 ((a) zero-tolerance on tensors); per-edge
    raw bond dim == 2^(chain multiplicity through that edge) ((a) construction
    identity; chain legs fuse multiplicatively without compression).
    """
    import quimb.tensor as qtn  # lazy: keep the module importable without quimb

    layout = PepoLayout.from_sched(sched)
    dev = torch.device(device)
    mm = int(m)
    if mm not in (0, 1):
        raise ValueError(f"logical index m must be 0 or 1 (got {m})")
    n = layout.n_data

    # 1. H-spread seed: per-site H|0> = (1, 1, 0)/sqrt(2), from the local formula.
    seed = qutrit_gate("H", dev)[:, 0].clone().contiguous()
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

    # 3. Logical-sector projector (I + (-1)^m Z_L)/2 — the parent's oracle wiring
    # (logical_z only for a Z-kind logical, else the {0:'Z'} fallback).
    lkind = str(getattr(sched, "logical_kind", "Z")).upper()
    logical = dict(sched.logical) if (lkind == "Z" and sched.logical) else {0: "Z"}
    _apply_chain_operator(ket, layout, logical, float((-1.0) ** mm), tag, dev)
    tr_m = _ket_norm_sq(ket, layout)
    tr_other = tr_stab - tr_m  # sectors are complementary: P_0 + P_1 = I on the stab space
    floor = NUMERICAL_ZERO * tr_stab
    if not (tr_m > floor and tr_other > floor):
        raise RuntimeError(
            f"codestate sector norm assert failed (BOTH m must be nonzero): "
            f"m={mm} sector {tr_m:.3e}, other sector {tr_other:.3e}, "
            f"stab-projected mass {tr_stab:.3e}")

    # structural |2>-mass zero on every site tensor (exact by construction; the
    # zero-tolerance construction guarantee; keep a cheap guard here.
    for pos in range(n):
        data, _inds = ket[pos]
        if float(data[2].abs().max()) > NUMERICAL_ZERO:
            raise RuntimeError(f"site {pos}: |2> row of the codestate ket is not zero")

    # SINGLE-WIRE finalize (no step 4): rename p{pos} -> k{pos} and the ket bonds
    # e{p}_{q} -> B{p}_{q}; materialize untouched grid edges at dim 1; scale each
    # site by the unit-NORM constant tr_m**(-1/(2n)).
    norm_scale = tr_m ** (-1.0 / (2.0 * n))
    tensors = []
    for pos in range(n):
        data, inds = ket[pos]
        data = (data * norm_scale).contiguous()
        pinds = [phys_name(pos) if nm == f"p{pos}" else nm for nm in inds]
        for q in layout.neighbors(pos):
            ename = _ket_bond_name(pos, q)
            bname = fused_bond_name(pos, q)
            if ename in pinds:
                pinds = [bname if x == ename else x for x in pinds]
            elif bname not in pinds:
                data = data.unsqueeze(-1)  # materialize the untouched grid edge (dim 1)
                pinds = pinds + [bname]
        tensors.append(qtn.Tensor(data=data.contiguous(), inds=tuple(pinds),
                                  tags={site_tag(pos)}))

    tn = qtn.TensorNetwork(tensors)
    return PepsState(tn=tn, layout=layout, device=str(device), ledger=[])


def dense_psi(state: PepsState) -> torch.Tensor:
    """Dense ``(3^n,)`` reconstruction of the PEPS for bounded d3 comparison.
    Engine position 0 is the
    MOST-significant qutrit factor; ``n_data <= 9`` assert kept; a d5 patch has NO
    dense bridge). The comparison against ``|psi><psi|`` is owned by tests;
    this function returns the vector only.
    """
    import quimb.tensor as qtn  # lazy: keep the module importable without quimb

    layout = state.layout
    n = layout.n_data
    assert n <= 9, f"dense_psi is the bounded d3 reference bridge only (n_data = {n} > 9)"

    sites = _site_tensors_by_pos(state.tn, n)
    tensors = [qtn.Tensor(data=sites[pos].data, inds=sites[pos].inds)
               for pos in range(n)]
    out_inds = tuple(phys_name(p) for p in range(n))
    res = qtn.TensorNetwork(tensors).contract(output_inds=out_inds)
    return res.data.reshape(-1)


# re-exported for the sibling modules (single source: the parent layout)
__all__ = [
    "CDTYPE",
    "RDTYPE",
    "QUTRIT",
    "PepoLayout",
    "PepsState",
    "apply_site_op",
    "build_codestate_peps",
    "dense_psi",
    "fused_bond_name",
    "phys_name",
    "qutrit_gate",
    "renormalize",
    "site_tag",
    "site_tensor",
    "_fuse_pair",
]

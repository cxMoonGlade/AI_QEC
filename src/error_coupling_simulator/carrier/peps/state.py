from __future__ import annotations

r"""Single-wire qutrit PEPS state + codestate builder (RUNG-B spike, module builder).

Binding doc: ``docs/nonpauli_teacher/peps_singlewire_spike_contract.md`` (v1.0
REGISTERED) — §2 (representation + op table), §3 (op registry), D3/D4 (naming +
reuse-over-rewrite). Parent geometry/chain machinery is IMPORTED from the ARCHIVED
``carrier/pepo`` package (single source; the pepo package itself is never modified):
``PepoLayout`` (SF2 — d-generic, VERBATIM), the ket-layer chain machinery
``_apply_chain_operator`` / ``_ket_norm_sq`` / ``_fuse_pair`` (SF1 — the codestate
ket layer is already single-wire; pepo steps 1–3), and ``_site_tensors_by_pos``.

SINGLE-WIRE finalization (SF1, NEW vs the parent): steps 1–3 only — the ket⊗bra
fuse (parent step 4) never happens. The physical leg stays dim **3** (named
``k{pos}``), ket bonds are renamed to the grid-edge names ``B{p}_{q}`` (D3: the
pepo naming carried over so reused machinery works unchanged), untouched grid
edges are materialized as dim-1 bonds, and the unit-NORM constant is
``tr_m**(-1/(2n))`` per site (the parent's ``tr_m**(-1/n)`` is
density-matrix-specific — SF1).

REFEREE INDEPENDENCE (D4 / §3 independence rule): this package shares NO code path
with ``carrier/exact/qutrit_dm`` — the qutrit gate table below (H/X/Y/Z/S/S_DAG on
the computational ``{|0>,|1>}`` block, leaked ``|2>`` inert) is built locally BY
FORMULA, mirroring the ``mps_forward._qutrit_gate`` value contract; the parent
layout's one referee import (``qudit_hadamard`` for the seed) is replaced by the
local formula here (D4).

GPU-only, torch-cuda-complex128 ALWAYS (SW-S8); devices passed in, never guessed.
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

#: qutrit local dimension — the SINGLE-WIRE physical leg (contract §2: dim 3, not 9).
QUTRIT = 3


# --------------------------------------------------------------------------- #
# Local single-qutrit gate table (referee-independent — D4)                    #
# --------------------------------------------------------------------------- #
def qutrit_gate(name: str, device, dtype=CDTYPE) -> torch.Tensor:
    """A single-qutrit FRAME gate ``(3,3)`` on the computational ``{0,1}`` block,
    ``|2>`` inert — the ``mps_forward._qutrit_gate`` value contract, built locally
    BY FORMULA (the engine shares no code path with the referee, contract §3)."""
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
    """The dim-3 physical index name at engine position ``pos`` (contract §2:
    ``k{pos}`` — the pepo NAME carried over, now dim 3 single-wire)."""
    return f"k{int(pos)}"


# --------------------------------------------------------------------------- #
# State object                                                                 #
# --------------------------------------------------------------------------- #
class PepsState:
    """The single-wire (pure-state) qutrit PEPS (contract §2).

    Attributes: ``tn`` (quimb ``TensorNetwork``; one rank<=5 site tensor per data
    qutrit, tagged ``Q{pos}``, physical index ``k{pos}`` of dim **3**, virtual
    bonds ``B{p}_{q}`` on the grid edges), ``layout`` (:class:`PepoLayout` —
    VERBATIM import, SF2), ``device`` (str), ``ledger`` (list of dicts in the
    pepo convention: discarded weight on the SQUARED-sigma RELATIVE scale, norm
    shifts logged). NO global gauge/canonical form is tracked. Positivity is
    STRUCTURAL (a pure state) — the parent's C3 negativity machinery is
    intentionally absent (contract §2); its audit role is the §6.2 per-read
    accuracy instruments + the norm ledger.

    Construction asserts (§2 / SW-S8): torch complex128 tensors on a cuda device,
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
                f"PepsState tensors are torch-cuda-complex128 ALWAYS (SW-S8); "
                f"got device {self.device!r}")
        sites = _site_tensors_by_pos(tn, layout.n_data)
        for pos in range(layout.n_data):
            t = sites[pos]
            data = t.data
            if not torch.is_tensor(data):
                raise TypeError(f"site {pos}: tensor data is not a torch tensor")
            if data.dtype != CDTYPE:
                raise TypeError(f"site {pos}: dtype {data.dtype} != complex128 (SW-S8)")
            if data.device.type != dev.type:
                raise ValueError(
                    f"site {pos}: tensor device {data.device} != state device {self.device}")
            if len(t.inds) > 5:
                raise ValueError(f"site {pos}: rank {len(t.inds)} > 5 (contract §2)")
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
    """The unique site tensor tagged ``Q{pos}`` (contract §2 tag convention)."""
    ts = state.tn.select_tensors(f"Q{int(pos)}", which="all")
    if len(ts) != 1:
        raise RuntimeError(f"expected exactly one tensor tagged Q{pos}, found {len(ts)}")
    return ts[0]


def apply_site_op(state: PepsState, pos: int, op: torch.Tensor) -> None:
    """Contract a ``(3,3)`` operator onto the physical leg ``k{pos}``.

    Single-site by construction — bond dims ASSERTED unchanged (contract §2 op
    table: 1-site gates and Kraus branches are bond-inert on a PEPS). The op is
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


def apply_gate_1site(state: PepsState, U: torch.Tensor, pos: int) -> None:
    """Apply a ``(3, 3)`` operator at engine position ``pos`` (contract §2 op-table
    row ``apply_gate_1site``) — the ``(state, U, pos)`` argument order. A thin
    alias of :func:`apply_site_op` (which takes ``(state, pos, op)``); NOT required
    to be unitary, so it also carries the SW1 forced-Kraus branch ``K_k psi``
    (unnormalized). Bond-inert (a 1-site op grows no bond)."""
    apply_site_op(state, int(pos), U)


def renormalize(state: PepsState, norm_sq: float) -> None:
    """Scale the state to unit norm given a measured ``<psi|psi>`` (the caller's
    read — exact or boundary route; the pre-scale value is the caller's ledger
    record). Raises on a collapsed (nonpositive) norm."""
    ns = float(norm_sq)
    if not ns > NUMERICAL_ZERO:
        raise RuntimeError(f"renormalize: nonpositive norm {ns:.6e} (state collapsed)")
    state.tn.multiply_(1.0 / (ns ** 0.5))


# --------------------------------------------------------------------------- #
# Codestate builder — pepo steps 1–3, single-wire finalization (SF1)           #
# --------------------------------------------------------------------------- #
def build_codestate_peps(sched, m: int, device: str = "cuda") -> PepsState:
    """Build the codestate ``|m>_L`` as a single-wire :class:`PepsState`.

    Contract §3 registry row "codestate steps 1–3 (ported)": the parent's ket
    layer VERBATIM (H-spread seed ``(1,1,0)/sqrt(2)``; per check ONE bond-2
    W-tensor chain ``(I + c.g)/2`` along ``plaquette_path`` in ``sched.stabilizers``
    order, then the logical-sector projector — the oracle's order; nonzero-norm
    ASSERTED for BOTH m sectors), with two single-wire changes:

      * the seed ``H|0>`` comes from the LOCAL gate formula (:func:`qutrit_gate`),
        never the referee's ``qudit_hadamard`` (D4 — the one parent referee import
        is replaced here);
      * NO ket⊗bra fuse (parent step 4): the physical leg stays dim 3, and the
        unit-NORM constant is ``tr_m**(-1/(2n))`` per site (SF1).

    Structural guarantees carried on the result (§2 op table): the ``k=2`` slice
    of every site tensor is exactly 0.0 ((a) zero-tolerance on tensors); per-edge
    raw bond dim == 2^(chain multiplicity through that edge) ((a) construction
    identity, SF1 — chain legs fuse MULTIPLICATIVELY, no compression).
    """
    import quimb.tensor as qtn  # lazy: keep the module importable without quimb

    layout = PepoLayout.from_sched(sched)
    dev = torch.device(device)
    mm = int(m)
    if mm not in (0, 1):
        raise ValueError(f"logical index m must be 0 or 1 (got {m})")
    n = layout.n_data

    # 1. H-spread seed: per-site H|0> = (1, 1, 0)/sqrt(2) — LOCAL formula (D4).
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
    # VERBATIM (logical_z only for a Z-kind logical, else the {0:'Z'} fallback).
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
    # (a) zero-tolerance guarantee of the §2 op table — cheap guard here).
    for pos in range(n):
        data, _inds = ket[pos]
        if float(data[2].abs().max()) > NUMERICAL_ZERO:
            raise RuntimeError(f"site {pos}: |2> row of the codestate ket is not zero")

    # SINGLE-WIRE finalize (no step 4): rename p{pos} -> k{pos} and the ket bonds
    # e{p}_{q} -> B{p}_{q}; materialize untouched grid edges at dim 1; scale each
    # site by the unit-NORM constant tr_m**(-1/(2n)) (SF1).
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
    """Dense ``(3^n,)`` reconstruction of the PEPS — the d3 referee bridge
    (contract §3: the ``layout.dense_rho`` convention — engine position 0 is the
    MOST-significant qutrit factor; ``n_data <= 9`` assert kept; a d5 patch has NO
    dense bridge). The SW0 dense compare (``|psi><psi|`` vs the referee's rho) is
    the gate script's, chunked — this returns the vector only.
    """
    import quimb.tensor as qtn  # lazy: keep the module importable without quimb

    layout = state.layout
    n = layout.n_data
    assert n <= 9, f"dense_psi is the d3 referee bridge only (n_data = {n} > 9)"

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
    "apply_gate_1site",
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

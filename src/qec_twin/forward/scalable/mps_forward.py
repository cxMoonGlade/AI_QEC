from __future__ import annotations

"""quimb MCWF-on-MPS FORWARD backend for the leakage surface-code teacher (ADR 0010, task 8c).

The **scaling lift** of the dense state-vector Monte-Carlo (MCWF) leakage forward
(``forward/scalable/sv_sampler.py`` + its ``forward/kernels/sv_traj_d3.cu`` kernel):
each shot is a pure-state quantum trajectory carried as a **qutrit Matrix-Product
State** (``phys_dim=3``, ``quimb`` torch backend on cuda, ``complex128``), Wood-Gambetta
leakage **Kraus-sampled** on the dim-3 physical leg, stabilizers **Born-sampled +
projected**, with each per-stabilizer measurement truncated at ``max_bond=chi`` and the
discarded weight tracked. The ensemble mean of the trajectories is the exact mixed
evolution (ADR 0010 forward carrier; the exact MPS lift of the project's dense MCWF and
of Manabe-Suzuki-Darmawan arXiv:2308.08186).

WHY an MPS lift (ADR 0010 Context). The exact ``3^n`` qutrit state-vector is
feasibility-only (d3 ``3^9`` fits; d5 ``3^25`` SV = 13.5 TB is dead). The surface-code
twin (d5/d7, the end goal) needs an area-law carrier; an MPS along a thin strip keeps the
bond ``chi`` small and constant in ``d`` (snake/boustrophedon ordering, ADR 0010 §Decision-4).
This backend is **d3 (then thin-strip-general)**; full ``d x d`` is deferred (ADR 0010 phasing).

FAITHFULNESS (docs/FAITHFULNESS_PROTOCOL.md; ADR 0010 constraint ledger C1-C8). This
backend REUSES, never reinvents, the load-bearing schedule physics of ``sv_sampler.py``:

  * the within-cycle marshalling (:class:`SvSampler.marshal_within_cycle` ->
    :class:`WithinCycleMarshalled`): the per-qutrit interleaved ``[H?] LEAK [H?] LEAK X
    LEAK [H?] LEAK M Y`` op stream, the per-CZ ``exp(L/4)`` leak slice, and -- critically
    (C5) -- **the per-round transversal X (mid-cycle) + Y (post-M) DD echoes**. Dropping
    those echoes inflated leakage 10-40x in a prior toy (FAITHFULNESS ledger #1); they are
    carried here exactly as the gate stream the host marshals;
  * the WG leakage Kraus (:func:`leak_slice_kraus_torch`, the single ``exp(Lindbladian)``
    source of truth), CPTP-asserted ``< 1e-12`` (C1);
  * the codestate ``|m>_L`` (:meth:`SvSampler.build_codestate`, the stabilizer+logical
    projection, ``<S>=+1`` / ``<L>=(-1)^m`` self-checked);
  * the ShotSet contract (:class:`ShotSet`, :meth:`SvSampler.pack_shots` /
    ``build_header`` / ``syndrome_bits_per_shot``) -- byte-identical to the dense backend.

The trajectory dynamics are the **exact MPS lift of ``sv_traj_wc_kernel``** (the within-
cycle kernel, ``sv_traj_d3.cu`` lines 685+): per round, the PRE-measure op segment (GATE
-> 1-site unitary; LEAK -> Kraus-sample the ``exp(L/4)`` slice), then the 8 stabilizer
Born-measurements (X-supports Hadamard-rotated to Z; arm-dependent ``d_q(2)``; sample
``s ~ <E_s>``; collapse ``sqrt(E_s)``), then the POST-measure Y segment (empty on the
terminal round); finally the per-qutrit biased-``b`` terminal readout (``sqrt(F_bit)``
collapse) -> ``logical_flip = parity XOR m``. The RNG draw ORDER matches the kernel's
``Section 5`` normative order so a host-pre-generated uniform stream reproduces the dense
engine bit-for-bit at full ``chi`` (the C8 anchor + the 8e certification hook).

Pure-MPS positivity is structural (C2 -- a trajectory is a pure state). Coherence is carried
exactly by the amplitudes (C4 -- ``C_L>0`` iff ``theta>0`` is a property of the WG Kraus,
unchanged by the MPS carrier at full ``chi``). The ONLY simplification is the bond
truncation; its per-cut discarded weight ``eps_cut`` (the Schmidt identity
``||psi - psi_chi||^2 = sum_{i>chi} sigma_i^2``, ADR 0010 Design-A, class (a)) is tracked
into :class:`MpsTruncationLedger` (the STATE-fidelity book; the LER/floor error map is the
separate 8e d3-DM-certified book, never merged -- ADR 0010 Design-A "two ledgers").

GPU-only MPS compute (binding; ADR 0010 R-GPU). ``complex128`` throughout (precision-first).
This phase keeps GPU use SMALL (a concurrent heavy DM job runs -- tiny self-checks only;
the full 9q rung-1 certification vs the DM is task 8e). The backend is a LIBRARY; every run
is a committed script under ``outputs/teacher_prereg/`` (scripted-execution HARD CONSTRAINT).

src/ commit-gate: STAGED, awaiting confirmation (mainline-code commit gate).
"""

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import torch

from qec_twin.forward.exact.xzzx_parser import XZZXSchedule
from qec_twin.forward.scalable.sv_sampler import (
    SV_ARM_CODE,
    SV_ARMS,
    SV_GATE_IDS,
    SV_READOUT_CODE,
    WC_OP_GATE,
    WC_OP_LEAK,
    RunSpec,
    ShotSet,
    SvSampler,
    WithinCycleMarshalled,
)
from qec_twin.numerics import NUMERICAL_ZERO

CDTYPE = torch.complex128
RDTYPE = torch.float64
PHYS = 3  # qutrit physical dimension

#: Default exact-grade bond cap: 3^ceil(L/2) is the largest Schmidt rank a qutrit MPS of
#: length L can carry, so chi >= 3^ceil(L/2) is EXACT (zero truncation). For d3 (L=9) that
#: is 3^5 = 243; the small self-validation runs at this (C8 zero-truncation exactness).
def exact_chi(n_sites: int) -> int:
    """The bond dimension at which an ``n_sites``-qutrit MPS is exact (no truncation)."""
    return int(PHYS ** ((int(n_sites) + 1) // 2))


# --------------------------------------------------------------------------- #
# Truncation ledger (ADR 0010 Design-A: the STATE-fidelity book, class (a)).   #
# --------------------------------------------------------------------------- #
@dataclass
class MpsTruncationLedger:
    """Per-cut discarded-weight accounting for the MCWF-MPS trajectories (class (a)).

    The Schmidt identity ``||psi - psi_chi||^2 = sum_{i>chi} sigma_i^2 = eps_cut`` bounds
    the STATE error of one truncation; over a trajectory ``1 - F <= sum_t eps_cut^(t)``
    (ADR 0010 Design-A). This is the STATE book ONLY -- it bounds the state, NOT the
    LER/floor (that is the separate d3-DM-certified ``eps <-> error`` map, task 8e; the two
    are NEVER merged). Each truncating op records its discarded weight (measured here as the
    norm loss of the post-truncation pure state: a unitary/gate keeps norm 1 at full chi, so
    ``1 - ||psi_chi||^2`` IS the discarded Schmidt weight of that cut).

    ``per_shot_total`` is the accumulated discarded weight of one trajectory; ``worst_cut``
    the single worst cut seen; ``n_truncating_ops`` the count of measurement ops that could
    truncate. ``ok`` is reported against a tolerance by the caller (C7 tripwire: refine chi
    and the floor/LER must converge -- monotone, no drift).
    """

    chi: int
    n_truncating_ops: int = 0
    worst_cut: float = 0.0
    sum_discarded: float = 0.0  # summed over all cuts in this ledger's lifetime
    n_shots: int = 0
    worst_shot_total: float = 0.0

    def record_cut(self, discarded: float) -> None:
        d = float(discarded)
        if d < 0.0:
            d = 0.0  # clamp float64 round-off below zero
        self.n_truncating_ops += 1
        self.sum_discarded += d
        if d > self.worst_cut:
            self.worst_cut = d

    def record_shot_total(self, shot_total: float) -> None:
        self.n_shots += 1
        if float(shot_total) > self.worst_shot_total:
            self.worst_shot_total = float(shot_total)

    def report(self) -> dict[str, Any]:
        return {
            "chi": int(self.chi),
            "exact_grade": bool(self.worst_cut <= NUMERICAL_ZERO),
            "n_truncating_ops": int(self.n_truncating_ops),
            "worst_cut_discarded_weight": float(self.worst_cut),
            "sum_discarded_weight": float(self.sum_discarded),
            "worst_shot_total_discarded": float(self.worst_shot_total),
            "n_shots": int(self.n_shots),
            "ledger_class": "(a) state-fidelity (Schmidt discarded weight); NOT the LER/floor "
                            "error map (that is the separate d3-DM-certified book, task 8e)",
        }


# --------------------------------------------------------------------------- #
# Snake (boustrophedon) site ordering (ADR 0010 Decision-4).                   #
# --------------------------------------------------------------------------- #
def snake_order_from_coords(coords: "tuple[tuple[float, ...], ...]") -> tuple[int, ...]:
    """Boustrophedon (snake) MPS site order over engine positions, from their grid coords.

    ADR 0010 Decision-4: snake along the SHORT lattice dimension so lattice-adjacent qutrits
    (which share a stabilizer) stay near each other in the 1D chain -> chi small + constant in
    ``d`` (area law). Returns ``order`` with ``order[k] = engine_position`` placed at MPS site
    ``k`` (a permutation of ``0..n-1``). The thin strip's SHORT axis is the one with fewer
    distinct coordinate values; the snake sweeps the short axis, reversing direction each step
    of the long axis (so consecutive MPS sites are spatially adjacent).

    Exactness is independent of the ordering (any permutation is exact at full chi); the order
    only controls the truncation efficiency. For d3 the chain is short enough that the order is
    immaterial to correctness -- it is implemented faithfully for the thin-strip-general scale.
    """
    n = len(coords)
    if n == 0:
        return ()
    xs = sorted({c[0] for c in coords})
    ys = sorted({c[1] for c in coords})
    # SHORT axis = fewer distinct values -> sweep it inside the snake.
    if len(xs) <= len(ys):
        long_vals, short_vals, long_axis, short_axis = ys, xs, 1, 0
    else:
        long_vals, short_vals, long_axis, short_axis = xs, ys, 0, 1
    pos_of: dict[tuple[float, float], int] = {(c[long_axis], c[short_axis]): i for i, c in enumerate(coords)}
    order: list[int] = []
    for li, lv in enumerate(long_vals):
        row_short = short_vals if (li % 2 == 0) else list(reversed(short_vals))
        for sv in row_short:
            key = (lv, sv)
            if key in pos_of:
                order.append(pos_of[key])
    # any position not placed by the grid sweep (defensive: ragged strips) appended in order.
    placed = set(order)
    for i in range(n):
        if i not in placed:
            order.append(i)
    if sorted(order) != list(range(n)):
        raise AssertionError(f"snake order {order} is not a permutation of 0..{n - 1}")
    return tuple(order)


# --------------------------------------------------------------------------- #
# Single-qutrit operator table (mirrors the kernel / DM-oracle gate set).      #
# --------------------------------------------------------------------------- #
def _qutrit_gate(name: str, device, dtype=CDTYPE) -> torch.Tensor:
    """A single-qutrit FRAME gate ``(3,3)`` on the computational ``{0,1}`` subspace,
    ``|2>`` inert -- IDENTICAL to ``qutrit_dm.single_qutrit_gate`` / the kernel's gate table
    (so the MPS forward, the DM oracle, and the SV kernel apply the same per-round gate)."""
    nm = str(name).upper()
    m = torch.zeros((PHYS, PHYS), dtype=dtype, device=device)
    if nm == "I":
        return torch.eye(PHYS, dtype=dtype, device=device)
    if nm == "H":
        inv2 = 1.0 / (2.0 ** 0.5)
        m[0, 0] = inv2; m[0, 1] = inv2; m[1, 0] = inv2; m[1, 1] = -inv2; m[2, 2] = 1.0
        return m
    if nm == "X":
        m[0, 1] = 1.0; m[1, 0] = 1.0; m[2, 2] = 1.0
        return m
    if nm == "Y":
        m[0, 1] = -1.0j; m[1, 0] = 1.0j; m[2, 2] = 1.0
        return m
    if nm == "Z":
        m[0, 0] = 1.0; m[1, 1] = -1.0; m[2, 2] = 1.0
        return m
    if nm == "S":
        # EXACT copy of qutrit_dm.single_qutrit_gate("S"): diag(1, i, 1), |2> inert.
        m[0, 0] = 1.0; m[1, 1] = 1.0j; m[2, 2] = 1.0
        return m
    if nm == "S_DAG":
        # EXACT copy of qutrit_dm.single_qutrit_gate("S_DAG"): diag(1, -i, 1), |2> inert.
        m[0, 0] = 1.0; m[1, 1] = -1.0j; m[2, 2] = 1.0
        return m
    raise ValueError(f"unsupported single-qutrit gate {name!r}")


def _arm_d2(arm: str, b: float) -> float:
    """The per-qutrit leaked-level Z-parity weight ``d_q(2)`` for a measurement arm
    (sv_traj_d3.cu ``measure_stab_block``): A/C -> ``1-2b``, B1 -> ``+1``, B2 -> ``-1``."""
    a = str(arm).upper()
    if a in ("A", "C"):
        return 1.0 - 2.0 * float(b)
    if a == "B1":
        return 1.0
    if a == "B2":
        return -1.0
    raise ValueError(f"unknown measurement arm {arm!r} (expected A, C, B1 or B2)")


# --------------------------------------------------------------------------- #
# The MCWF-on-MPS forward backend                                             #
# --------------------------------------------------------------------------- #
class MpsLeakageForward:
    """quimb MCWF-on-MPS forward backend for the d3 (thin-strip-general) leakage teacher.

    ``sample(spec, chi) -> ShotSet``: parse -> marshal the within-cycle schedule (REUSING
    :class:`SvSampler`) -> build the ``|m>_L`` MPS codestate -> run ``N`` MCWF trajectories
    on the MPS (one shot each) -> pack the ShotSet (byte-identical to the dense backend).

    The trajectory body is the exact MPS lift of ``sv_traj_wc_kernel`` (see the module
    docstring): per round PRE-ops (GATE/LEAK) -> 8 stabilizer Born-measurements -> POST-ops
    (Y; empty terminal) -> terminal readout. The per-stabilizer measurement is the only
    bond-growing op; it is truncated at ``max_bond=chi`` and its discarded weight recorded.

    GPU-only; ``complex128``. KEEP GPU USE SMALL this phase (task 8c is BUILD + a tiny
    self-validation; the full 9q rung-1 certification vs the DM is task 8e).
    """

    def __init__(self, device: str | torch.device = "cuda") -> None:
        self.device = torch.device(device)
        # the dense backend's host driver: the SINGLE source of the schedule marshalling,
        # the WG leak slice, the codestate, and the ShotSet pack/header (REUSE, not reinvent).
        self._host = SvSampler(device=self.device)
        # lazy quimb import so the module imports without quimb present (mirrors sv_sampler's
        # lazy kernel guard); the GPU MCWF path requires it.
        import quimb.tensor as qtn  # noqa: WPS433

        self._qtn = qtn

    # ----------------------------------------------------------------------- #
    # MPS construction                                                         #
    # ----------------------------------------------------------------------- #
    def _mps_from_statevector(self, psi: torch.Tensor, order: tuple[int, ...]):
        """Build a snake-ordered qutrit MPS from a dense ``3^n`` engine state vector.

        ``psi`` is in the ENGINE basis (qutrit ``p`` = the ``p``-th most-significant tensor
        factor; quimb ``from_dense`` with ``dims=[3]*n`` uses the SAME row-major / site-0-MSB
        convention -- verified against the engine index map). ``order[k] = engine_position``
        placed at MPS site ``k`` (the snake permutation); the dense tensor is transposed into
        snake-site order BEFORE the MPS factorization so MPS site ``k`` carries engine qutrit
        ``order[k]``. ``from_dense`` is EXACT (full Schmidt rank), so this is a zero-truncation
        lift (the C8 anchor). All arrays are moved to torch cuda complex128.
        """
        n = len(order)
        psi_t = psi.reshape([PHYS] * n)
        # transpose engine axes -> snake-site axes: site k reads engine axis order[k].
        psi_snake = psi_t.permute(*order).contiguous().reshape(-1)
        arr = psi_snake.detach().cpu().numpy()
        mps = self._qtn.MatrixProductState.from_dense(arr, dims=[PHYS] * n)
        mps.apply_to_arrays(lambda x: torch.as_tensor(x, dtype=CDTYPE, device=self.device))
        return mps

    @staticmethod
    def _norm_sq(mps) -> float:
        """``<psi|psi>`` (real) of a quimb MPS via a cuda contraction."""
        return float((mps.H & mps).contract(all).real)

    @staticmethod
    def _renormalize(mps, norm_sq: float | None = None) -> float:
        """Scale the MPS to unit norm; return the pre-scale ``<psi|psi>`` (the branch weight)."""
        ns = MpsLeakageForward._norm_sq(mps) if norm_sq is None else float(norm_sq)
        if ns > NUMERICAL_ZERO:
            inv = 1.0 / (ns ** 0.5)
            mps.multiply_(inv, spread_over=1)  # scalar onto one tensor (exact)
        return ns

    # ----------------------------------------------------------------------- #
    # Local reads on the MPS (expectations of single-/multi-site diagonals)    #
    # ----------------------------------------------------------------------- #
    def _site_population(self, mps, mps_site: int, level: int) -> float:
        """``<psi| (|level><level| on mps_site) |psi> / <psi|psi>`` -- the level-``level``
        population on one MPS site (used for the MCWF leak branch norms + arm-C leak flags)."""
        proj = torch.zeros((PHYS, PHYS), dtype=CDTYPE, device=self.device)
        proj[int(level), int(level)] = 1.0
        ket = mps.copy()
        ket.gate_(proj, where=int(mps_site), contract=True)
        num = float((mps.H & ket).contract(all).real)
        den = self._norm_sq(mps)
        return num / den if den > NUMERICAL_ZERO else 0.0

    def _parity_expectation(self, mps, supp_sites: list[int], d2: float) -> float:
        """``<psi| prod_q D_q |psi> / <psi|psi>`` for the diagonal parity string
        ``D_q = diag(1, -1, d2)`` on the (already Z-rotated) support MPS sites.

        A product of single-site diagonal operators -> the expectation factorizes through the
        MPS contraction (apply each D_q as a 1-site gate to a ket copy, overlap with the bra).
        This is the ``<P>`` the kernel reduces (``measure_stab_block``) to get
        ``p(s=0) = 1/2 (1 + <P>)``.
        """
        Dq = torch.diag(torch.tensor([1.0, -1.0, float(d2)], dtype=CDTYPE, device=self.device))
        ket = mps.copy()
        for s in supp_sites:
            ket.gate_(Dq, where=int(s), contract=True)
        num = float((mps.H & ket).contract(all).real)
        den = self._norm_sq(mps)
        return num / den if den > NUMERICAL_ZERO else 0.0

    # ----------------------------------------------------------------------- #
    # Trajectory steps (exact MPS lift of the kernel's __device__ routines)    #
    # ----------------------------------------------------------------------- #
    def _apply_gate(self, mps, U: torch.Tensor, mps_site: int) -> None:
        """1-site unitary on ``mps_site`` (exact; no truncation -- a 1-site gate cannot grow
        the bond). The MPS lift of ``apply_gate_block``."""
        mps.gate_(U, where=int(mps_site), contract=True)

    def _leak_sample(self, mps, kraus: list[torch.Tensor], mps_site: int, u: float) -> None:
        """MCWF Kraus-sample the leak slice on ``mps_site`` (the MPS lift of
        ``leakage_sample_block``): branch ``k`` w.p. ``p_k = ||K_k psi||^2`` (CPTP =>
        ``sum_k p_k = <psi|psi>``), then ``psi <- K_k psi / sqrt(p_k)``. ONE uniform ``u``
        consumed (Section-5 order). A 1-site Kraus cannot grow the bond -> exact, no truncation.

        ``p_k`` is read by overlap with the bra of ``K_k`` applied to a ket copy (no dense
        ``3^n`` state). The selected branch is applied in place + renormalized.
        """
        den = self._norm_sq(mps)
        pk = []
        for K in kraus:
            ket = mps.copy()
            ket.gate_(K, where=int(mps_site), contract=True)
            pk.append(self._norm_sq(ket))  # ||K psi||^2
        tot = float(sum(pk))
        target = float(u) * tot
        cum = 0.0
        sel = len(pk) - 1
        for k, p in enumerate(pk):
            cum += p
            if target <= cum:
                sel = k
                break
        mps.gate_(kraus[sel], where=int(mps_site), contract=True)
        self._renormalize(mps, norm_sq=pk[sel])

    def _measure_stabilizer(
        self, mps, supp_sites: list[int], isx: list[int], d2: float, u_outcome: float,
        chi: int, ledger: MpsTruncationLedger,
        *, arm: str = "A", u_leakflags: list[float] | None = None,
    ) -> tuple[int, float]:
        """One stabilizer Born-measurement on the MPS (the lift of ``measure_stab_block``).

        Steps, mirroring the kernel exactly:
          1. rotate X-type support sites to Z (1-site Hadamard; ``|2>`` inert);
          2. (arm C only) leak-flag projection onto a sampled leak pattern over the support
             (one uniform per support site, support order; projects ``|2>`` vs ``{0,1}`` per
             site) -- the same-``E_s``, maximal-leakage-disturbance comparator;
          3. ``<P> = <prod_q D_q>``, ``p(s=0) = 1/2 (1 + <P>)``; sample ``s`` (ONE uniform);
          4. apply ``sqrt(E_s)`` where ``E_s = 1/2 (I + (-1)^s prod_q D_q)`` -- built as the
             EXACT dense ``sqrt`` on the (<=4-site) support and applied as a multi-site gate
             with ``max_bond=chi`` truncation; the discarded weight is recorded;
          5. renormalize; rotate the X-supports back.

        Returns ``(sampled syndrome bit, discarded Schmidt weight)``. ``sqrt(E_s)`` over
        disjoint support sites is the proper square-root POVM instrument (its ensemble mean is
        the DM-oracle Luders update), so the MPS forward matches the dense engine at full ``chi``.
        """
        H = _qutrit_gate("H", self.device)
        x_sites = [supp_sites[j] for j in range(len(supp_sites)) if int(isx[j]) == 1]
        for s in x_sites:
            self._apply_gate(mps, H, s)

        if str(arm).upper() == "C":
            flags = list(u_leakflags or [])
            if len(flags) < len(supp_sites):
                raise ValueError("arm C needs one leak-flag uniform per support site")
            for j, site in enumerate(supp_sites):
                p2 = self._site_population(mps, site, 2)
                lf = 1 if (float(flags[j]) < p2) else 0
                # project: keep |2> iff lf else keep {0,1} (a 1-site diagonal projector)
                if lf:
                    proj = torch.diag(torch.tensor([0.0, 0.0, 1.0], dtype=CDTYPE, device=self.device))
                else:
                    proj = torch.diag(torch.tensor([1.0, 1.0, 0.0], dtype=CDTYPE, device=self.device))
                mps.gate_(proj, where=int(site), contract=True)
                self._renormalize(mps)  # renorm after the leak-flag projection

        p_par = self._parity_expectation(mps, supp_sites, d2)  # <P>
        p0 = 0.5 * (1.0 + p_par)
        sbit = 0 if (float(u_outcome) < p0) else 1

        discarded = self._apply_sqrt_Es(mps, supp_sites, d2, sbit, chi, ledger)
        ledger.record_cut(discarded)

        for s in x_sites:
            self._apply_gate(mps, H, s)
        return int(sbit), float(discarded)

    def _apply_sqrt_Es(
        self, mps, supp_sites: list[int], d2: float, sbit: int, chi: int,
        ledger: MpsTruncationLedger,
    ) -> float:
        """Apply ``sqrt(E_s)`` on the support and return the discarded Schmidt weight of the cut.

        ``E_s`` is diagonal in the trit basis with ``E_s[c] = 1/2 (1 + (-1)^s prod_q d_q(t_q))``
        (``d_q`` from :func:`_arm_d2`). It factorizes over the support but ``sqrt`` of the
        ``1/2(1 +/- prod)`` does NOT, so it is built as the EXACT dense diagonal ``sqrt(E_s)`` on
        the support qutrits (``3^w``, ``w <= 4`` for d3 -- trivially small) and applied as ONE
        multi-site gate via quimb ``contract='nonlocal'`` (the ONLY mode that handles >2 (and
        non-contiguous) support sites AND re-compresses the resulting state bond at
        ``max_bond=chi`` -- ``swap+split``/``auto-split-gate`` either reject >2 sites or do not
        truncate the post-application state bond, verified). The discarded weight is the norm gap
        between the EXACT (full-chi) and the truncated post-measurement pure state at this cut.

        For the projector arms (B1/B2; A at ``b in {0,1}``) ``sqrt(E_s) = E_s`` is the exact
        parity projector; for fractional ``b`` it is the proper biased square-root POVM Kraus.
        Returns the discarded weight (``0`` at exact-grade ``chi``).
        """
        w = len(supp_sites)
        # build the diagonal sqrt(E_s) over the support trit-tuples (3^w), row-major with
        # support[0] the most-significant factor (matches quimb's site ordering of the gate legs).
        d_levels = torch.tensor([1.0, -1.0, float(d2)], dtype=RDTYPE, device=self.device)
        # enumerate the 3^w configs; prod of d over sites; E_s; sqrt.
        grids = torch.meshgrid(*([torch.arange(PHYS, device=self.device)] * w), indexing="ij")
        prod = torch.ones([PHYS] * w, dtype=RDTYPE, device=self.device)
        for g in grids:
            prod = prod * d_levels[g]
        sgn = 1.0 if int(sbit) == 0 else -1.0
        es = 0.5 * (1.0 + sgn * prod)
        es = torch.clamp(es, min=0.0)
        sqrt_es = torch.sqrt(es).reshape(-1).to(CDTYPE)
        G = torch.diag(sqrt_es)  # (3^w, 3^w) diagonal multi-site gate

        where = tuple(int(s) for s in supp_sites)
        if int(chi) >= exact_chi(mps.L):
            # exact-grade chi: NO truncation is possible (chi >= full Schmidt rank), so the
            # discarded weight is structurally 0 -- skip the (costly) reference apply (this is
            # the C8 path the self-validation + the rung-1 exact-grade certification use).
            mps.gate_(G, where=where, contract="nonlocal", max_bond=int(chi), cutoff=0.0)
            self._renormalize(mps)
            return 0.0
        # truncating chi: measure the discarded Schmidt mass as the norm gap between the EXACT
        # (full-chi) and the truncated post-measurement pure state at this cut. The EXACT branch
        # weight (== Tr[E_s rho] for a normalized input) comes from a full-chi apply on a copy.
        exact = mps.copy()
        exact.gate_(G, where=where, contract="nonlocal", max_bond=exact_chi(mps.L), cutoff=0.0)
        norm_exact = self._norm_sq(exact)
        mps.gate_(G, where=where, contract="nonlocal", max_bond=int(chi), cutoff=0.0)
        norm_trunc = self._norm_sq(mps)
        self._renormalize(mps, norm_sq=norm_trunc)
        if norm_exact > NUMERICAL_ZERO:
            discarded = max(0.0, (norm_exact - norm_trunc) / norm_exact)
        else:
            discarded = 0.0
        return float(discarded)

    def _terminal_readout(
        self, mps, log_sites: list[int], log_isx: list[int], n_data: int,
        b_eff: float, m: int, u_draws: list[float],
    ) -> int:
        """The terminal transversal data readout (lift of ``terminal_readout_block``).

        Rotate logical X-supports to Z; then for every data qutrit (MPS-site order matching the
        kernel's ``q=0..n-1`` ENGINE order -> mapped through the snake), sample its computational
        bit with the biased-``b`` POVM ``F1=|1><1|+b|2><2|`` (``P(bit=1)=<F1>``) and collapse
        with ``sqrt(F_bit)`` (``|2>`` kept at ``sqrt(b_eff)`` / ``sqrt(1-b_eff)``, NOT full
        weight). The logical flip is ``parity(sampled bits over the logical support) XOR m``.
        One uniform per data qutrit (Section-5 terminal draw order, engine-qutrit order).
        """
        H = _qutrit_gate("H", self.device)
        x_log = [log_sites[j] for j in range(len(log_sites)) if int(log_isx[j]) == 1]
        for s in x_log:
            self._apply_gate(mps, H, s)

        qbit: dict[int, int] = {}
        # the draw order is ENGINE-qutrit order q=0..n-1; map each to its MPS site below.
        for q in range(int(n_data)):
            mps_site = self._eng_to_mps[q]
            # P(bit=1) = <F1>, F1 diag weight [t==1] + b_eff*[t==2]
            F1 = torch.diag(torch.tensor([0.0, 1.0, float(b_eff)], dtype=CDTYPE, device=self.device))
            ket = mps.copy()
            ket.gate_(F1, where=int(mps_site), contract=True)
            w1 = float((mps.H & ket).contract(all).real)
            wt = self._norm_sq(mps)
            p1 = (w1 / wt) if wt > NUMERICAL_ZERO else 0.5
            bit = 1 if (float(u_draws[q]) < p1) else 0
            qbit[q] = bit
            # collapse sqrt(F_bit): {0,1} trit matching bit -> 1, other {0,1} -> 0, |2| ->
            # sqrt(b_eff) (bit 1) / sqrt(1-b_eff) (bit 0).
            if bit == 1:
                diag = torch.tensor([0.0, 1.0, float(b_eff) ** 0.5], dtype=CDTYPE, device=self.device)
            else:
                diag = torch.tensor([1.0, 0.0, (1.0 - float(b_eff)) ** 0.5], dtype=CDTYPE, device=self.device)
            mps.gate_(torch.diag(diag), where=int(mps_site), contract=True)
            self._renormalize(mps)

        parity = 0
        # logical support is given in ENGINE positions; XOR the sampled engine-qutrit bits.
        for q in self._log_eng_support:
            parity ^= (qbit[q] & 1)
        return int((parity ^ (int(m) & 1)) & 1)

    # ----------------------------------------------------------------------- #
    # One trajectory (the lift of sv_traj_wc_kernel)                          #
    # ----------------------------------------------------------------------- #
    def _run_trajectory(
        self, codestate_mps, marsh: WithinCycleMarshalled, leak_kraus: list[torch.Tensor],
        gate_table: dict[int, torch.Tensor], stab_supp: np.ndarray, stab_isx: np.ndarray,
        stab_len: np.ndarray, log_sites_eng: list[int], log_isx: list[int],
        arm: str, b: float, b_eff: float, m: int, chi: int, n_data: int, R: int,
        rng: np.random.Generator, ledger: MpsTruncationLedger,
    ) -> tuple[list[int], int, float]:
        """Evolve ONE pure-MPS trajectory; return (syndrome bits round-major, logical_flip,
        shot_discarded_total). The RNG draw order mirrors ``sv_traj_wc_kernel`` Section-5."""
        mps = codestate_mps.copy()
        d2 = _arm_d2(arm, b)
        round_op_ptr = marsh.round_op_ptr.detach().cpu().numpy()
        op_kind = marsh.op_kind.detach().cpu().numpy()
        op_uid = marsh.op_uid.detach().cpu().numpy()
        op_site = marsh.op_site.detach().cpu().numpy()
        syndrome_bits: list[int] = []
        shot_discarded = 0.0

        for r in range(int(R)):
            # PRE-measure op segment (GATE / LEAK), CSR order -- draws consumed as walked.
            pre0, pre1 = int(round_op_ptr[2 * r]), int(round_op_ptr[2 * r + 1])
            for t in range(pre0, pre1):
                site_eng = int(op_site[t])
                mps_site = self._eng_to_mps[site_eng]
                if int(op_kind[t]) == WC_OP_GATE:
                    self._apply_gate(mps, gate_table[int(op_uid[t])], mps_site)
                elif int(op_kind[t]) == WC_OP_LEAK:
                    u = float(rng.random())
                    self._leak_sample(mps, leak_kraus, mps_site, u)
                else:
                    raise AssertionError(f"unknown op_kind {int(op_kind[t])} at op {t}")
            # measure all stabilizers (schedule order); X-supports rotated to Z inside.
            for s_idx in range(int(marsh.n_stab)):
                slen = int(stab_len[s_idx])
                supp_eng = [int(stab_supp[s_idx, k]) for k in range(slen)]
                supp_mps = [self._eng_to_mps[e] for e in supp_eng]
                isx = [int(stab_isx[s_idx, k]) for k in range(slen)]
                u_lf = None
                if str(arm).upper() == "C":
                    u_lf = [float(rng.random()) for _ in range(slen)]
                u_out = float(rng.random())
                bit, disc = self._measure_stabilizer(
                    mps, supp_mps, isx, d2, u_out, chi, ledger, arm=arm, u_leakflags=u_lf)
                syndrome_bits.append(int(bit))
                shot_discarded += float(disc)
            # POST-measure op segment (the transversal Y; empty terminal round). No draws.
            post0, post1 = int(round_op_ptr[2 * r + 1]), int(round_op_ptr[2 * r + 2])
            for t in range(post0, post1):
                site_eng = int(op_site[t])
                mps_site = self._eng_to_mps[site_eng]
                if int(op_kind[t]) == WC_OP_GATE:
                    self._apply_gate(mps, gate_table[int(op_uid[t])], mps_site)
                elif int(op_kind[t]) == WC_OP_LEAK:
                    u = float(rng.random())
                    self._leak_sample(mps, leak_kraus, mps_site, u)

        # terminal readout draws (engine-qutrit order q=0..n-1)
        u_term = [float(rng.random()) for _ in range(int(n_data))]
        flip = self._terminal_readout(mps, log_sites_eng, log_isx, n_data, b_eff, m, u_term)
        return syndrome_bits, int(flip), float(shot_discarded)

    # ----------------------------------------------------------------------- #
    # The public sampler                                                      #
    # ----------------------------------------------------------------------- #
    def sample(
        self, spec: RunSpec, *, sched: XZZXSchedule | None = None, chi: int | None = None,
        materialize: bool = True, snake: bool = True,
    ) -> tuple[ShotSet, MpsTruncationLedger]:
        """Run an MCWF-on-MPS forward job: parse -> marshal -> codestate -> N trajectories ->
        ShotSet (byte-identical to the dense backend) + the truncation ledger.

        REUSES :class:`SvSampler` for the schedule marshalling (the within-cycle CSR with the
        X/Y DD echoes -- C5), the WG leak slice (CPTP-asserted -- C1), the codestate (``<S>``/
        ``<L>`` self-checked), and the ShotSet pack/header. The within-cycle path REQUIRES the
        per-qutrit interior streams; pass a ``sched`` that already has them attached (the
        r01-geometry + r10-interior-streams split, model §1):
        ``sched = parse_xzzx_circuit(r01).with_within_cycle_streams(parse_within_cycle_streams(r10))``.
        ``sched=None`` parses ``spec.circuit_path`` directly (only works if that circuit is
        itself multi-round so its interior streams populate).

        ``chi`` is the bond cap (default exact-grade ``3^ceil(L/2)`` -> zero truncation,
        the C8 anchor). ``snake`` selects the boustrophedon site order (ADR 0010 Decision-4);
        exactness is order-independent at full ``chi``. GPU-only; ``complex128``.
        """
        if not torch.cuda.is_available():
            raise RuntimeError("GPU-only contract: CUDA must be available for the MCWF-MPS forward")
        sched = self._host.parse(spec) if sched is None else sched
        if not sched.within_cycle_streams:
            raise ValueError(
                "MpsLeakageForward (within-cycle) requires sched.within_cycle_streams "
                "(a MULTI-ROUND source circuit's interior streams). Attach them via "
                "sched.with_within_cycle_streams(parse_within_cycle_streams(r10_circuit)) -- "
                "the r01-geometry + r10-interior split (model §1).")

        leak_t, _leak_ev = self._host.build_within_cycle_leak(spec)  # CPTP + compose asserted (C1)
        leak_kraus = [leak_t[k] for k in range(leak_t.shape[0])]
        marsh = self._host.marshal_within_cycle(sched, leak_t, R=spec.R)
        codestate, code_evidence = self._host.build_codestate(sched, spec.m)  # <S>/<L> asserted

        n_data = int(marsh.n_data)
        R = int(marsh.R)
        # site ordering (snake or identity); build the engine<->mps maps.
        order = snake_order_from_coords(sched.data_coords) if snake else tuple(range(n_data))
        self._mps_order = order
        self._eng_to_mps = {eng: site for site, eng in enumerate(order)}
        self._log_eng_support = [int(x) for x in marsh.log_supp.detach().cpu().numpy().tolist()]

        chi_eff = int(chi) if chi is not None else exact_chi(n_data)
        ledger = MpsTruncationLedger(chi=chi_eff)

        codestate_mps = self._mps_from_statevector(codestate, order)

        # gate table (engine SV_GATE_IDS) -> the (3,3) cuda unitaries (mirrors the kernel table).
        from qec_twin.forward.scalable.sv_sampler import SV_GATE_NAMES
        gate_table = {SV_GATE_IDS[name]: _qutrit_gate(name, self.device) for name in SV_GATE_NAMES}

        stab_supp = marsh.stab_supp.detach().cpu().numpy()
        stab_isx = marsh.stab_supp_isx.detach().cpu().numpy()
        stab_len = marsh.stab_supp_len.detach().cpu().numpy()
        log_sites_eng = self._log_eng_support
        log_isx = marsh.log_supp_isx.detach().cpu().numpy().tolist()

        b_eff = 0.5 if str(spec.readout_conv) == "half" else float(spec.b)
        n_stab = int(marsh.n_stab)
        N = int(spec.N)
        syndromes = np.zeros((N, n_stab * R), dtype=np.uint8)
        flips = np.zeros((N,), dtype=np.uint8)

        for shot in range(N):
            # per-shot RNG keyed by (base_seed, shot) -- a wave-layout-independent stream
            # (the host-side analog of the kernel's per-shot Philox keying).
            rng = np.random.default_rng((int(spec.base_seed), shot))
            bits, flip, shot_disc = self._run_trajectory(
                codestate_mps, marsh, leak_kraus, gate_table, stab_supp, stab_isx, stab_len,
                log_sites_eng, log_isx, str(spec.arm).upper(), float(spec.b), b_eff,
                int(spec.m), chi_eff, n_data, R, rng, ledger)
            syndromes[shot, :] = np.asarray(bits, dtype=np.uint8)
            flips[shot] = np.uint8(flip)
            ledger.record_shot_total(shot_disc)

        packed = self._host.pack_shots(syndromes, flips)
        # the dense backend's header (byte-identical ShotSet); marshal_schedule gives the
        # MarshalledSchedule the header reader expects (gate-CSR view + logical support).
        marsh_lumped = self._host.marshal_schedule(sched, R=spec.R)
        header = self._host.build_header(spec, marsh_lumped, sched)
        header["backend"] = "mps_mcwf/quimb"
        header["mps_chi"] = int(chi_eff)
        header["mps_chi_exact_grade"] = int(exact_chi(n_data))
        header["mps_snake_order"] = list(order)
        header["mps_truncation_ledger"] = ledger.report()
        header["codestate_check"] = code_evidence

        bits_per_shot = self._host.syndrome_bits_per_shot(n_stab, R)
        out_path = None
        header_path = None
        if spec.out_path is not None:
            from pathlib import Path
            import json
            out_path = Path(spec.out_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            header_path = out_path.with_suffix(out_path.suffix + ".header.json")
            header_path.write_text(json.dumps(header, indent=2))
            with open(out_path, "wb") as fh:
                fh.write(np.ascontiguousarray(packed).tobytes())

        shotset = ShotSet(
            header=header,
            path=out_path,
            header_path=header_path,
            n_shots=N,
            syndrome_bits_per_shot=bits_per_shot,
            diag={"mps_truncation": ledger.report()},
            shots=(packed if materialize else None),
        )
        return shotset, ledger

    # ----------------------------------------------------------------------- #
    # Self-validation helper: the FULL-chi forward distribution on the MPS     #
    # ----------------------------------------------------------------------- #
    def forward_state_dense(
        self, spec: RunSpec, *, sched: XZZXSchedule | None = None, snake: bool = True,
    ) -> torch.Tensor:
        """The codestate as a dense ``3^n`` torch vector reconstructed FROM the MPS (full chi),
        in ENGINE basis order -- the C8 self-validation hook (compare to the from-scratch /
        ``qutrit_dm`` dense codestate). Builds the snake MPS then contracts it back + inverts
        the snake permutation, so the returned vector is directly comparable to the engine SV.
        """
        sched = self._host.parse(spec) if sched is None else sched
        order = snake_order_from_coords(sched.data_coords) if snake else tuple(range(sched.n_data))
        codestate, _ = self._host.build_codestate(sched, spec.m)
        mps = self._mps_from_statevector(codestate, order)
        dense_snake = torch.as_tensor(mps.to_dense(), dtype=CDTYPE, device=self.device).reshape(
            [PHYS] * sched.n_data)
        # invert the snake permutation: engine axis e sits at snake site order.index(e).
        inv = [order.index(e) for e in range(sched.n_data)]
        return dense_snake.permute(*inv).contiguous().reshape(-1)

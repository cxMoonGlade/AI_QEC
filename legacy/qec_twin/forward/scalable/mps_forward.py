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

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np
import torch

from qec_twin.forward.exact.xzzx_parser import XZZXSchedule
from qec_twin.forward.scalable.sv_sampler import (
    CPTP_TOL,
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

if TYPE_CHECKING:  # pragma: no cover - typing only
    from qec_twin.forward.scalable.soft_readout import SoftReadoutModel

CDTYPE = torch.complex128
RDTYPE = torch.float64
PHYS = 3  # qutrit physical dimension


# --------------------------------------------------------------------------- #
# Terminal-readout result (D2 soft-emission contract §2): the per-shot terminal #
# emission the three modes produce. ``flip`` (all modes) is the logical flip    #
# ``parity(bit(k_bar) over the logical support) XOR m`` (== ⑦'s in hard2 and in #
# DISTRIBUTION on the level path); ``levels`` (hard3/soft) the per-data-qutrit   #
# realized level k_bar in {0,1,2} (ENGINE order q=0..n-1); ``iq`` (soft) the     #
# per-data-qutrit IQ point z (n_data,2) float64 from the soft emitter.           #
# --------------------------------------------------------------------------- #
@dataclass
class TerminalReadout:
    """One shot's terminal-readout emission (the three D2 modes; see _terminal_readout).

    ``flip`` int 0/1; ``bits`` a length-``n_data`` list of the per-data-qutrit COMPUTATIONAL bit
    (engine order; ALL modes — ⑦'s F1 bit in hard2, ``bit(k_bar)`` on the level path); ``levels`` a
    length-``n_data`` list of k_bar in {0,1,2} (engine order; ``None`` for hard2); ``iq`` a
    ``(n_data, 2)`` cuda float64 tensor (soft only; ``None`` otherwise). ``bits`` is the
    L-soft-1 per-qubit statistic (⑦'s F1 bit-marginal vs the level-path hardened bit-marginal).
    """

    flip: int
    bits: "list[int] | None" = None
    levels: "list[int] | None" = None
    iq: "torch.Tensor | None" = None

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


#: Largest ``n_data`` for which the dense ``3^n`` codestate lift (``_mps_from_statevector``) is
#: built; above this the DIRECT MPS codestate (``build_codestate_mps_direct``) is used (d5=25,
#: d7=49 cannot be built densely). 3^12 ≈ 0.5M amplitudes (8.5 MB) is the dense-feasible ceiling.
DENSE_CODESTATE_MAX = 12

#: Bond cap for the DIRECT codestate build. The codestate is a stabilizer state; on the FULL-SQUARE
#: Google patches the bond grows as 2^(2*distance) (d3=64=2^6, d5=1024=2^10 -- MEASURED), built at
#: ``min(exact_chi, CODESTATE_CHI_CAP)`` so it starts EXACT (eps_cut 0), SEPARATELY from the (smaller)
#: dynamics bond ``chi``. d5 (2^10) is exact + feasible under this cap. ⚠ FULL-SQUARE d7's codestate
#: is 2^14=16384 > this cap -> it would truncate BELOW rank (the L2 "codestate exact" leg FAILS at
#: full-square d7 by construction), AND a bond-16384 MPS over 49 sites (~630 GB) is INFEASIBLE: this
#: is exactly the ADR-0010 "single MPS chi~exp(d), dead at d7" regime. FULL-SQUARE d7 is NOT a target;
#: d7 needs the THIN-STRIP geometry (ADR-0010's actual phasing: chi small + constant in d). (A better
#: site ordering than the current snake -- which empirically gives 2x the minimal boundary -- could
#: lower the constant but not the exponent.)
CODESTATE_CHI_CAP = 8192


def _pauli_string_operator(kinds: "list[str]", device, dtype=CDTYPE) -> torch.Tensor:
    """``∏_q P_q`` as a dense ``(3^w, 3^w)`` operator (kron, site-0 = MSB), each ``P_q`` the engine
    single-qutrit Pauli (:func:`_qutrit_gate`; |2> inert) -- the SAME convention the dense
    ``QutritDM._codestate_vector`` stabilizer/logical projectors use, so the direct MPS codestate
    matches the dense codestate bit-for-bit (validated, p8)."""
    g = None
    for kind in kinds:
        P = _qutrit_gate(str(kind).upper(), device, dtype=dtype)
        g = P if g is None else torch.kron(g, P)
    return g


def _eigenspace_projector(kinds: "list[str]", eigen: int, device, dtype=CDTYPE) -> torch.Tensor:
    """``(I + eigen·∏P_q)/2`` -- the ``eigen``-eigenspace projector of a single-type Pauli string,
    dense on the ``w``-site support (``w <= 4`` -> <= 81x81)."""
    g = _pauli_string_operator(kinds, device, dtype=dtype)
    eye = torch.eye(g.shape[0], dtype=dtype, device=device)
    return (eye + float(eigen) * g) * 0.5


def _with_gesvd_svd(method):
    """Decorator: run ``method`` with cuda ``torch.linalg.svd`` routed through the gesvd (QR) driver.

    quimb's MPS-truncation SVDs hit cusolver's DEFAULT driver (gesvdj/auto), which is SLOWER than the
    explicit gesvd driver and can hard-error (CUSOLVER_STATUS_INVALID_VALUE) on the NEAR-DEGENERATE
    (stabilizer-flat) Schmidt spectra the MCWF trajectory produces -- the "failed to converge" ->
    slow-accurate-fallback storm. The SVD speedup is SIZE-DEPENDENT: ~5-11x at the d5-relevant
    192-768 matrix sizes, up to ~21x on larger/very-degenerate matrices (measured,
    ``outputs/teacher_prereg/p9c_svd_bench.py``); per-shot this cut d5 chi=64 ~222 -> ~104 s/shot
    (the RESIDUAL is quimb gate_nonlocal per-op overhead + the serial per-shot loop, NOT the SVD --
    so d5/d7 PRODUCTION scale is INFEASIBLE without the deferred batched-shot/SVD work).
    gesvd (QR) is robust + fast. The swap is
    SCOPED to the wrapped call (restored in ``finally``) so torch's global default is untouched
    elsewhere; single-threaded (the per-shot trajectory loop) so the global swap is safe here.
    ``driver=`` is cuda-only -> CPU tensors fall through unchanged."""
    import functools
    import os

    @functools.wraps(method)
    def _wrapped(*args, **kwargs):
        # QEC_MPS_SVD_DRIVER overrides the driver (default 'gesvd'); 'default'/'cusolver'/'off' leaves
        # torch's default (used by the Q5 gesvd-vs-default record-invariance A/B; production = gesvd).
        drv = os.environ.get("QEC_MPS_SVD_DRIVER", "gesvd").lower()
        if drv in ("default", "cusolver", "off", ""):
            return method(*args, **kwargs)
        orig = torch.linalg.svd

        def _svd(A, full_matrices=True, *, driver=None, out=None):
            if getattr(A, "is_cuda", False) and driver is None:
                driver = drv
            return orig(A, full_matrices=full_matrices, driver=driver, out=out)

        torch.linalg.svd = _svd
        try:
            return method(*args, **kwargs)
        finally:
            torch.linalg.svd = orig

    return _wrapped


# --------------------------------------------------------------------------- #
# Dense statevector <-> MPS lift (public form; ownership contract row A3)      #
# --------------------------------------------------------------------------- #
# CONVENTION: site-0-MSB (engine qutrit p = p-th most-significant tensor factor)
def mps_from_statevector(psi: torch.Tensor, order: tuple[int, ...], device):
    """Build a site-ordered qutrit MPS from a dense ``3^n`` ENGINE-basis state vector.

    The module-level public form of :meth:`MpsLeakageForward._mps_from_statevector`
    (which delegates here -- behavior-identical: same quimb calls, same convention).

    ``psi`` is in the ENGINE basis -- site-0-MSB: engine qutrit ``p`` is the ``p``-th
    MOST-significant tensor factor of the ``3^n`` vector; quimb ``from_dense`` with
    ``dims=[3]*n`` uses the SAME row-major / site-0-MSB convention (verified against
    the engine index map). ``order[k] = engine_position`` placed at MPS site ``k``
    (the snake permutation); the dense tensor is transposed into site order BEFORE the
    MPS factorization so MPS site ``k`` carries engine qutrit ``order[k]``.
    ``from_dense`` is EXACT (full Schmidt rank), so this is a zero-truncation lift
    (the C8 anchor). All arrays land on ``device`` as torch complex128. Lazy quimb
    import (mirrors the class's lazy import; the module imports without quimb).
    """
    import quimb.tensor as qtn  # lazy: keep the module importable without quimb

    n = len(order)
    psi_t = psi.reshape([PHYS] * n)
    # transpose engine axes -> site axes: site k reads engine axis order[k].
    psi_snake = psi_t.permute(*order).contiguous().reshape(-1)
    arr = psi_snake.detach().cpu().numpy()
    # CONVENTION: site-0-MSB -- from_dense(dims=[3]*n) reads arr row-major, so tensor
    # factor 0 (engine qutrit order[0]) is the most-significant axis.
    mps = qtn.MatrixProductState.from_dense(arr, dims=[PHYS] * n)
    mps.apply_to_arrays(lambda x: torch.as_tensor(x, dtype=CDTYPE, device=device))
    return mps


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

        Delegates to the module-level public form :func:`mps_from_statevector`
        (behavior-identical refactor: same quimb calls, same site-0-MSB convention;
        see the convention anchor there). ``order[k] = engine_position`` placed at MPS
        site ``k`` (the snake permutation). ``from_dense`` is EXACT (full Schmidt
        rank), so this is a zero-truncation lift (the C8 anchor). All arrays are moved
        to torch cuda complex128 on ``self.device``.
        """
        return mps_from_statevector(psi, order, self.device)

    def attach_layout(self, order: tuple[int, ...], logical_support: list[int]) -> None:
        """Bind the engine<->MPS site maps + logical support for direct method use.

        Sets ``_mps_order`` (MPS site ``k`` carries engine qutrit ``order[k]``),
        ``_eng_to_mps`` (engine position -> MPS site), and ``_log_eng_support`` (the
        logical observable's engine-position support) EXACTLY as :meth:`sample` does
        (:meth:`sample` routes through this method -- behavior-identical refactor,
        row A3). Call it before driving the trajectory/measurement methods directly
        (referee-side harness use: ``_run_trajectory`` / ``_measure_stabilizer`` /
        ``_terminal_readout`` all read these maps). ``order`` must be a permutation of
        ``0..len(order)-1`` (the snake or identity site order); ``logical_support``
        is the engine-position list (e.g. ``marsh.log_supp`` as ints).

        DIRECTION CONVENTION (site->engine): ``order[k]`` = the engine position
        carried at MPS site ``k``; ``_eng_to_mps`` is its INVERSE (engine position
        -> MPS site). NON-identity example::

            order = (2, 0, 1)   # MPS site 0 carries engine qutrit 2, site 1 -> 0, site 2 -> 1
            _eng_to_mps == {2: 0, 0: 1, 1: 2}

        ``order`` must be a SEQUENCE. A ``Mapping`` (e.g. the ``eng_to_mps`` dict) is
        REJECTED with :class:`TypeError`: iterating a dict yields its KEYS only, so a
        total eng->mps dict would always pass the permutation check while silently
        reinterpreting key INSERTION ORDER as the site->engine order (K-6 hazard).
        """
        if isinstance(order, Mapping):
            raise TypeError(
                "order must be a sequence with order[k] = engine position at MPS "
                "site k (site->engine); got a Mapping — pass the ORDER TUPLE, not "
                "the eng_to_mps dict")
        order_t = tuple(int(x) for x in order)
        if sorted(order_t) != list(range(len(order_t))):
            raise ValueError(
                f"attach_layout: order must be a permutation of 0..{len(order_t) - 1} "
                f"(got {order!r})")
        self._mps_order = order_t
        self._eng_to_mps = {eng: site for site, eng in enumerate(order_t)}
        self._log_eng_support = [int(x) for x in logical_support]

    def build_codestate_mps_direct(self, sched: "XZZXSchedule", m: int, chi: int,
                                   order: "tuple[int, ...]", eng_to_mps: "dict[int, int]"):
        """Build ``|m>_L`` DIRECTLY as a snake-ordered MPS -- NO dense ``3^n`` intermediate (the
        d5/d7 scale unblock; the dense ``_mps_from_statevector(build_codestate(...))`` path is
        d3-only). Mirrors the EXACT dense formula (``QutritDM._codestate_vector``) bit-for-bit:

            |m>_L  ∝  ( ∏_g (I+g)/2 ) · ( I + (-1)^m Z_L )/2 · |+...+>

        seed |+...+> a bond-1 product MPS; each ≤4-site projector ``(I+eigen·∏P_q)/2`` applied via
        the validated ``gate_(where, contract='nonlocal', max_bond=chi)`` (the ``_apply_sqrt_Es``
        path), supports snake-mapped. A surface-code codestate is a qubit stabilizer state embedded
        in qutrits -> Schmidt rank 2^(boundary) (d3 bond 64, d5 bond 1024), so it is EXACT at a
        feasible ``chi`` (eps_cut 0). VALIDATED exact vs the independent dense codestate at d3 +
        structurally (<S_g>=+1, <Z_L>=(-1)^m, AND ``leak_mass``=0 -- TOGETHER a complete cert on the
        FULL 3^n space; <S>=+1 ALONE is complete only on {0,1}^n since the |2>-inert stabiliser Paulis
        make every |2>-containing state a +1 eigenstate) at d3 AND real d5
        (``outputs/teacher_prereg/p8_mps_codestate_direct.py``).

        Returns ``(mps, evidence)`` -- ``evidence`` carries the structural <S>/<L> residuals (the
        ``code_evidence`` :meth:`sample` records; NO dense state is built to check it) + the
        codestate's own truncation (``codestate_eps_cut``: 0 iff ``chi`` >= the codestate bond)."""
        n = int(sched.n_data)
        exact_grade = exact_chi(n)
        cs_worst_cut = 0.0
        # seed |+...+> : |0>^n product MPS (bond 1) -> H on every site (the dense seed H^n|0>).
        z0 = np.zeros(PHYS, dtype=np.complex128)
        z0[0] = 1.0
        mps = self._qtn.MPS_product_state([z0] * n)
        mps.apply_to_arrays(lambda x: torch.as_tensor(x, dtype=CDTYPE, device=self.device))
        H = _qutrit_gate("H", self.device)
        for site in range(n):  # product seed -> snake order irrelevant for the uniform |+...+>
            self._apply_gate(mps, H, site)

        def _project(kinds, supp_eng, eigen):
            nonlocal cs_worst_cut
            G = _eigenspace_projector(list(kinds), int(eigen), self.device)
            where = tuple(int(eng_to_mps[int(q)]) for q in supp_eng)
            if int(chi) >= exact_grade:  # no truncation possible -> skip the (costly) reference apply
                mps.gate_(G, where=where, contract="nonlocal", max_bond=int(chi), cutoff=0.0)
                self._renormalize(mps)
                return
            ref = mps.copy()
            ref.gate_(G, where=where, contract="nonlocal", max_bond=exact_grade, cutoff=0.0)
            # LOW-1 guard (review): the discarded-weight is only correct if the exact-grade reference
            # is GENUINELY exact (not itself truncated). A w<=4 projector grows the rank by <= 3^4, so
            # the reference bond stays far below exact_grade -- assert it (else norm_exact under-reports).
            assert max(ref.bond_sizes()) < exact_grade, \
                f"reference apply saturated max_bond=exact_grade={exact_grade} -> norm_exact truncated"
            ne = self._norm_sq(ref)
            mps.gate_(G, where=where, contract="nonlocal", max_bond=int(chi), cutoff=0.0)
            nt = self._norm_sq(mps)
            self._renormalize(mps, norm_sq=nt)
            disc = max(0.0, (ne - nt) / ne) if ne > NUMERICAL_ZERO else 0.0
            cs_worst_cut = max(cs_worst_cut, disc)

        for stab in sched.stabilizers:
            supp_eng = sorted(stab.paulis.keys())
            kinds = [stab.paulis[q] for q in supp_eng]
            if len({str(k).upper() for k in kinds}) != 1:
                raise ValueError(f"stabilizer not single-type (X or Z): {dict(stab.paulis)}")
            _project(kinds, supp_eng, +1)
        log_eng = sorted(sched.logical.keys())
        _project(["Z"] * len(log_eng), log_eng, (-1) ** int(m))

        # STRUCTURAL evidence (the complete cert for a pure normalized MPS; no dense state built):
        # <S_g> = +1 ∀g and <Z_L> = (-1)^m  <=>  the MPS IS |m>_L.
        den = self._norm_sq(mps)
        worst_S = 0.0
        for stab in sched.stabilizers:
            supp_eng = sorted(stab.paulis.keys())
            g = _pauli_string_operator([stab.paulis[q] for q in supp_eng], self.device)
            ket = mps.copy()
            ket.gate_(g, where=tuple(int(eng_to_mps[int(q)]) for q in supp_eng), contract="nonlocal")
            sg = complex((mps.H & ket).contract(all)) / den if den > NUMERICAL_ZERO else 0.0
            worst_S = max(worst_S, abs(sg - 1.0))
        zket = mps.copy()
        zket.gate_(_pauli_string_operator(["Z"] * len(log_eng), self.device),
                   where=tuple(int(eng_to_mps[int(q)]) for q in log_eng), contract="nonlocal")
        zl = complex((mps.H & zket).contract(all)) / den if den > NUMERICAL_ZERO else 0.0
        target = float((-1) ** int(m))
        # |2>-mass on the codestate. The stabilizers/logical are |2>-INERT Paulis, so EVERY
        # |2>-containing state is a +1 eigenstate of all of them -> <S_g>=+1 ∧ <Z_L>=(-1)^m alone
        # does NOT witness |2> contamination (it is a complete cert ONLY on the {0,1}^n subspace).
        # The construction seeds from H^n|0> (zero |2> mass) and |2>-inert projectors never inject
        # |2>, so the codestate provably has 0 |2> mass -- but we VERIFY that premise here (it is the
        # missing leg that makes <S>/<Z_L> a complete certification of |m>_L on the FULL 3^n space).
        leak_mass = float(sum(self._site_population(mps, st, 2) for st in range(n)))
        evidence = {
            "construction": "direct_mps_projector",
            "worst_S_residual": float(worst_S),
            "logical_expectation": float(zl.real),
            "logical_target": target,
            "worst_L_residual": float(abs(zl - target)),
            "leak_mass": leak_mass,  # total <|2>> population; 0 <=> zero |2> support (HIGH-1 premise)
            "max_bond": int(max(mps.bond_sizes())) if n > 1 else 1,
            "codestate_eps_cut": float(cs_worst_cut),
        }
        return mps, evidence

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
        # local canonical expectation (NOT a full-chain overlap) -- 1-site projector population.
        return float(mps.local_expectation_canonical(proj, int(mps_site), normalized=True).real)

    def _parity_expectation(self, mps, supp_sites: list[int], d2: float) -> float:
        """``<psi| prod_q D_q |psi> / <psi|psi>`` for the diagonal parity string
        ``D_q = diag(1, -1, d2)`` on the (already Z-rotated) support MPS sites.

        A product of single-site diagonal operators -> the expectation factorizes through the
        MPS contraction (apply each D_q as a 1-site gate to a ket copy, overlap with the bra).
        This is the ``<P>`` the kernel reduces (``measure_stab_block``) to get
        ``p(s=0) = 1/2 (1 + <P>)``.
        """
        # <prod_q D_q> via quimb's CANONICAL-form local expectation over the (<=4-site) support --
        # local, NOT the full-chain overlap the old code did (the measure was ~51% of the wall, p10).
        Dq = torch.diag(torch.tensor([1.0, -1.0, float(d2)], dtype=CDTYPE, device=self.device))
        G = None
        for _ in supp_sites:
            G = Dq if G is None else torch.kron(G, Dq)
        return float(mps.local_expectation_canonical(
            G, tuple(int(s) for s in supp_sites), normalized=True).real)

    # ----------------------------------------------------------------------- #
    # Trajectory steps (exact MPS lift of the kernel's __device__ routines)    #
    # ----------------------------------------------------------------------- #
    def _apply_gate(self, mps, U: torch.Tensor, mps_site: int) -> None:
        """1-site unitary on ``mps_site`` (exact; no truncation -- a 1-site gate cannot grow
        the bond). The MPS lift of ``apply_gate_block``."""
        mps.gate_(U, where=int(mps_site), contract=True)

    def _leak_sample(self, mps, kraus: list[torch.Tensor], mps_site: int, u: float) -> int:
        """MCWF Kraus-sample the leak slice on ``mps_site`` (the MPS lift of
        ``leakage_sample_block``): branch ``k`` w.p. ``p_k = ||K_k psi||^2`` (CPTP =>
        ``sum_k p_k = <psi|psi>``), then ``psi <- K_k psi / sqrt(p_k)``. ONE uniform ``u``
        consumed (Section-5 order). A 1-site Kraus cannot grow the bond -> exact, no truncation.

        RETURNS the selected branch index ``sel`` (int) -- a PURE addition (row A3):
        draws, selection, application, and renormalization are byte-identical to the
        pre-return code; only the already-computed index is surfaced (for referee-side
        harnesses; kills the ``_cumsel`` replica + its silent tie-break-drift trap).
        TIE-BREAK REGISTRY (``docs/twin_validation/batched_mps_backend_prereg.md``
        v2/v5, cited verbatim -- binding at this return-value definition): the selected
        branch is the FIRST ``k`` satisfying ``u * tot <= cumsum_k`` (NON-STRICT
        ``<=``; the strict-vs-nonstrict split is registered -- a ``<`` drift is the
        K-3 bug class), with fallback ``K - 1`` when float accumulation leaves no
        ``k`` satisfying it.

        ``p_k`` is read from the 1-site REDUCED DENSITY MATRIX (ONE local contraction), NOT n_kraus
        full-chain overlaps: since ``K_k`` is single-site, ``p_k = ||K_k psi||^2 = <psi|K_k^dag K_k|
        psi> = Tr[K_k^dag K_k rho_i]`` with ``rho_i = Tr_{j!=i}|psi><psi|`` the 1-site RDM (trace =
        <psi|psi>, so the p_k are the SAME unnormalized branch norms). This was the dominant per-shot
        cost (p10 profile: the leak was ~70% of the wall, ~441 ms/call, doing n_kraus full 25-site
        contractions at the codestate bond); the RDM is one contraction + trivial 3x3 traces.
        """
        # p_k = ||K_k psi||^2 = <psi| K_k^dag K_k |psi> via quimb's CANONICAL-form local expectation
        # (normalized=False -> the UNNORMALIZED <psi|op|psi>, matching the old branch norms exactly).
        # The shared ``info`` dict caches the orthogonality center across the n_kraus calls so the MPS
        # is canonicalized to the site ONCE -> the expectation is LOCAL, NOT the n_kraus full 25-site
        # overlaps the old code did at the codestate bond (p10 profile: the leak was ~70% of the wall).
        site = int(mps_site)
        info: dict = {}
        pk = [float(mps.local_expectation_canonical(
                    K.conj().transpose(-1, -2) @ K, site, normalized=False, info=info).real)
              for K in kraus]
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
        return int(sel)

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
        *, mode: str = "hard2", soft_model: "SoftReadoutModel | None" = None,
        gen: "np.random.Generator | None" = None, b_bit: float | None = None,
    ) -> "TerminalReadout":
        """The terminal transversal data readout (lift of ``terminal_readout_block``).

        Three modes (D2 soft-emission contract §2; the WITHIN-CYCLE path is UNTOUCHED — the
        terminal is the LAST op, post-state discarded, so there is no backaction; L-soft-4 is
        satisfied by construction):

        * ``mode='hard2'`` (DEFAULT — ⑦'s biased-bit terminal, byte-identical). For every data
          qutrit (ENGINE order ``q=0..n-1`` -> MPS site via the snake) sample its computational
          bit with the biased-``b`` POVM ``F1=|1><1|+b|2><2|`` (``P(bit=1)=<F1>``) using ONE
          uniform ``u_draws[q]`` and collapse ``sqrt(F_bit)``. The flip is ``parity(bit over the
          logical support) XOR m``. This is the EXACT ⑦ path: it consumes the SAME ``n_data``
          uniforms in the SAME engine order, so on a matched seed the syndrome record + the flip
          are bit-for-bit identical to the unmodified carrier (L-soft-8).
        * ``mode in {'hard3','soft'}`` (the FAITHFUL level path). Realize each data qutrit's LEVEL
          ``k_bar in {0,1,2}`` by the 3-OUTCOME PROJECTIVE measurement
          ``{|0><0|,|1><1|,|2><2|}`` — Born-sample ``k_bar`` from the current MPS level
          populations ``(p0,p1,p2)`` using ONE uniform ``u_draws[q]`` (engine order), then
          collapse ``|k_bar><k_bar|``. Both F1 and (projective-then-bit) are DIAGONAL in the
          level basis, so the joint OUTCOME distribution depends only on ``diag(rho)`` and
          ``bit(k_bar)`` (0->0, 1->1, 2->Bernoulli(b)) reproduces F1's joint bit distribution
          EXACTLY (this is why L-soft-1 holds: hard-2-via-level == ⑦'s F1 terminal in
          distribution). ``hard3`` reports the per-qutrit levels ``k_bar``; ``soft`` additionally
          emits the per-qutrit IQ ``z = soft_model.draw_iq(levels, gen)`` (consuming the SAME
          ``gen``, AFTER all level draws — see the explicit draw order below). The flip label is
          still computed from ``bit(k_bar)`` for bookkeeping (the decoder/floor recompute it from
          ``k_bar``/``z``).

        RNG DRAW ORDER (the seam/floor seed-matching contract — C and D3 depend on this):
          1. the LEVEL/bit draws: ``n_data`` uniforms, ENGINE-qutrit order ``q=0..n-1`` (one per
             qutrit). ``hard2`` reads them from ``u_draws`` (== ⑦'s pre-drawn ``u_term``);
             ``hard3``/``soft`` ALSO read them from ``u_draws`` (the caller pre-draws the SAME
             ``n_data`` uniforms in the SAME order, so the level path and the hard-2 path consume
             the host stream identically up to the terminal — L-soft-8 byte-identity of the
             syndrome record holds regardless, the syndrome draws all precede the terminal).
          2. ``soft`` ONLY: ONE additional batched IQ draw ``soft_model.draw_iq(levels, gen)``
             over the ``(n_data,)`` realized levels -> ``(n_data, 2)`` standard-normals from
             ``gen``, consumed AFTER step 1. The level realization is therefore IDENTICAL between
             ``hard3`` and ``soft`` on a matched seed (the IQ draw is downstream, additive output).

        Returns a :class:`TerminalReadout` carrying the flip (all modes) + the per-qutrit
        ``levels`` (hard3/soft, engine order) + ``iq`` (soft, engine order).
        """
        mode = str(mode)
        if mode not in ("hard2", "hard3", "soft"):
            raise ValueError(f"_terminal_readout mode must be hard2/hard3/soft (got {mode!r})")
        if mode == "soft" and soft_model is None:
            raise ValueError("mode='soft' requires a soft_model (the SoftReadoutModel emitter)")
        if mode == "soft" and gen is None:
            raise ValueError("mode='soft' requires gen (the per-shot numpy Generator for draw_iq)")
        # the bit-bias used to map a realized |2> to a computational bit (Bernoulli(b)) on the
        # level path; defaults to b_eff so hard-2-via-level reproduces the F1=diag(0,1,b_eff)
        # terminal. (b_eff is 0.5 under the 'half' readout convention, else the run's b.)
        b_for_bit = float(b_eff) if b_bit is None else float(b_bit)

        H = _qutrit_gate("H", self.device)
        x_log = [log_sites[j] for j in range(len(log_sites)) if int(log_isx[j]) == 1]
        for s in x_log:
            self._apply_gate(mps, H, s)

        qbit: dict[int, int] = {}
        levels: list[int] = [0] * int(n_data)  # engine-qutrit order q=0..n-1
        # the draw order is ENGINE-qutrit order q=0..n-1; map each to its MPS site below.
        for q in range(int(n_data)):
            mps_site = self._eng_to_mps[q]
            u = float(u_draws[q])
            if mode == "hard2":
                # ⑦'s biased-bit POVM F1=diag(0,1,b_eff); P(bit=1)=<F1>. ONE uniform -> bit.
                F1 = torch.diag(torch.tensor([0.0, 1.0, float(b_eff)], dtype=CDTYPE,
                                             device=self.device))
                ket = mps.copy()
                ket.gate_(F1, where=int(mps_site), contract=True)
                w1 = float((mps.H & ket).contract(all).real)
                wt = self._norm_sq(mps)
                p1 = (w1 / wt) if wt > NUMERICAL_ZERO else 0.5
                bit = 1 if (u < p1) else 0
                qbit[q] = bit
                # collapse sqrt(F_bit): {0,1} trit matching bit -> 1, other {0,1} -> 0, |2| ->
                # sqrt(b_eff) (bit 1) / sqrt(1-b_eff) (bit 0).
                if bit == 1:
                    diag = torch.tensor([0.0, 1.0, float(b_eff) ** 0.5], dtype=CDTYPE,
                                        device=self.device)
                else:
                    diag = torch.tensor([1.0, 0.0, (1.0 - float(b_eff)) ** 0.5], dtype=CDTYPE,
                                        device=self.device)
                mps.gate_(torch.diag(diag), where=int(mps_site), contract=True)
                self._renormalize(mps)
            else:
                # FAITHFUL 3-outcome projective level read: Born-sample k_bar from (p0,p1,p2),
                # collapse |k_bar><k_bar|. ONE uniform -> level (engine order).
                wt = self._norm_sq(mps)
                p = [0.0, 0.0, 0.0]
                # populations only on a live state: the quimb normalized read divides by
                # the trace UNCONDITIONALLY, so a zero-norm state (an annihilated branch)
                # yields NaN populations that shadow the tot-guard below (NaN <=
                # NUMERICAL_ZERO is False -> kbar falls through to 2). Skipping the read
                # keeps p = 0 -> tot = 0 -> kbar = 0, the batched arm's normative
                # degenerate semantics (per-shot mask, no NaN).
                if wt > NUMERICAL_ZERO:
                    for lev in (0, 1, 2):
                        p[lev] = self._site_population(mps, mps_site, lev)  # <|lev><lev|>/<psi|psi>
                # Born-sample by the cumulative populations (renormalized defensively).
                tot = float(p[0] + p[1] + p[2])
                if tot <= NUMERICAL_ZERO:
                    kbar = 0
                else:
                    target = u * tot
                    cum = 0.0
                    kbar = 2
                    for lev in (0, 1, 2):
                        cum += p[lev]
                        if target < cum:
                            kbar = lev
                            break
                levels[q] = int(kbar)
                # collapse onto the realized level (|k_bar><k_bar|).
                proj = torch.zeros((PHYS, PHYS), dtype=CDTYPE, device=self.device)
                proj[kbar, kbar] = 1.0
                mps.gate_(proj, where=int(mps_site), contract=True)
                self._renormalize(mps)
                # bit(k_bar): 0->0, 1->1, 2->Bernoulli(b_for_bit). The |2> bit is drawn from the
                # SAME host stream so the level path's bit distribution == F1's (L-soft-1). The
                # extra |2| draw is consumed ONLY when k_bar==2 (rare), keeping the common-case
                # one-draw-per-qutrit order aligned with hard-2; the |2| sub-draw uses gen when
                # provided (soft) else a deterministic split of u (hard3 standalone).
                if kbar == 2:
                    if gen is not None:
                        u2 = float(gen.random())
                    else:
                        # hard3 without gen: split the level uniform's residual within the |2>
                        # mass to a [0,1) bit uniform (deterministic, reproducible).
                        lo = float(p[0] + p[1]) / tot if tot > NUMERICAL_ZERO else 0.0
                        u2 = (u - lo) / max(p[2] / tot, NUMERICAL_ZERO) if tot > NUMERICAL_ZERO else 0.5
                        u2 = min(max(u2, 0.0), 1.0)
                    qbit[q] = 1 if (u2 < b_for_bit) else 0
                else:
                    qbit[q] = int(kbar)  # 0->0, 1->1

        parity = 0
        # logical support is given in ENGINE positions; XOR the sampled engine-qutrit bits.
        for q in self._log_eng_support:
            parity ^= (qbit[q] & 1)
        flip = int((parity ^ (int(m) & 1)) & 1)

        iq = None
        if mode == "soft":
            # ONE batched IQ draw over the realized levels (engine order), consuming gen AFTER
            # all level draws (the documented order). draw_iq returns (n_data, 2) float64 cuda.
            lev_t = torch.as_tensor(levels, dtype=torch.long, device=self.device)
            iq = soft_model.draw_iq(lev_t, gen)  # (n_data, 2)

        lev_out = None if mode == "hard2" else list(levels)
        bits_out = [int(qbit[q]) for q in range(int(n_data))]  # engine-order per-qutrit bit (all modes)
        return TerminalReadout(flip=flip, bits=bits_out, levels=lev_out, iq=iq)

    # ----------------------------------------------------------------------- #
    # One trajectory (the lift of sv_traj_wc_kernel)                          #
    # ----------------------------------------------------------------------- #
    def _run_trajectory(
        self, codestate_mps, marsh: WithinCycleMarshalled, leak_by_round: "list[list[torch.Tensor]]",
        gate_table: dict[int, torch.Tensor], stab_supp: np.ndarray, stab_isx: np.ndarray,
        stab_len: np.ndarray, log_sites_eng: list[int], log_isx: list[int],
        arm: str, b: float, b_eff: float, m: int, chi: int, n_data: int, R: int,
        rng: np.random.Generator, ledger: MpsTruncationLedger,
        *, mode: str = "hard2", soft_model: "SoftReadoutModel | None" = None,
    ) -> "tuple[list[int], TerminalReadout, float]":
        """Evolve ONE pure-MPS trajectory; return (syndrome bits round-major, TerminalReadout,
        shot_discarded_total). The RNG draw order mirrors ``sv_traj_wc_kernel`` Section-5; the
        WITHIN-CYCLE path (leak/gate/measure draws) is IDENTICAL for all terminal modes (the
        terminal is the LAST op), so on a matched seed the syndrome record is byte-identical
        across modes (L-soft-8). ``mode``/``soft_model`` only change the terminal emission.

        ``leak_by_round`` (P2-ii; prereg ``p2_conjunction_wiring_prereg.md`` §1 API pin) is the
        PER-ROUND leak-slice sequence: round ``r``'s WC_OP_LEAK ops Kraus-sample from
        ``leak_by_round[r]`` — BOTH the PRE-measure and the POST-measure segment of round ``r``
        (registered convention; today's post segments carry only the transversal Y, so the post
        leg is dormant but pinned). A single-set caller passes the SAME list for every round
        (``[base] * R``): the op stream, draw order, and record are then byte-identical to the
        static arm (gate P2-ii (a))."""
        mps = codestate_mps.copy()
        d2 = _arm_d2(arm, b)
        round_op_ptr = marsh.round_op_ptr.detach().cpu().numpy()
        op_kind = marsh.op_kind.detach().cpu().numpy()
        op_uid = marsh.op_uid.detach().cpu().numpy()
        op_site = marsh.op_site.detach().cpu().numpy()
        syndrome_bits: list[int] = []
        shot_discarded = 0.0

        for r in range(int(R)):
            leak_kraus_r = leak_by_round[r]  # round r's slice table (P2-ii per-round seam)
            # PRE-measure op segment (GATE / LEAK), CSR order -- draws consumed as walked.
            pre0, pre1 = int(round_op_ptr[2 * r]), int(round_op_ptr[2 * r + 1])
            for t in range(pre0, pre1):
                site_eng = int(op_site[t])
                mps_site = self._eng_to_mps[site_eng]
                if int(op_kind[t]) == WC_OP_GATE:
                    self._apply_gate(mps, gate_table[int(op_uid[t])], mps_site)
                elif int(op_kind[t]) == WC_OP_LEAK:
                    u = float(rng.random())
                    self._leak_sample(mps, leak_kraus_r, mps_site, u)
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
                    self._leak_sample(mps, leak_kraus_r, mps_site, u)

        # terminal readout draws (engine-qutrit order q=0..n-1): ONE level/bit uniform per data
        # qutrit, drawn from the SAME host stream as ⑦ (so the level path and the hard-2 path
        # consume the stream identically up to the terminal; the syndrome record is byte-identical
        # across modes — L-soft-8). For soft, the IQ draw (one batched draw_iq over the realized
        # levels) consumes ``rng`` AFTER these, inside _terminal_readout (the documented order).
        u_term = [float(rng.random()) for _ in range(int(n_data))]
        term = self._terminal_readout(
            mps, log_sites_eng, log_isx, n_data, b_eff, m, u_term,
            mode=mode, soft_model=soft_model, gen=rng)
        return syndrome_bits, term, float(shot_discarded)

    # ----------------------------------------------------------------------- #
    # The public sampler                                                      #
    # ----------------------------------------------------------------------- #
    @_with_gesvd_svd
    def sample(
        self, spec: RunSpec, *, sched: XZZXSchedule | None = None, chi: int | None = None,
        materialize: bool = True, snake: bool = True,
        mode: str = "hard2", soft_model: "SoftReadoutModel | None" = None,
        codestate_mode: str = "auto",
        leak_slices: "list[torch.Tensor] | tuple[torch.Tensor, ...] | None" = None,
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

        TERMINAL MODE (D2 soft-emission contract §2). ``mode in {'hard2','hard3','soft'}`` selects
        the terminal-readout emission (see :meth:`_terminal_readout`): ``hard2`` (default) is ⑦'s
        biased-bit terminal (the packed ShotFlip + syndrome are byte-identical to the unmodified
        carrier on a matched seed); ``hard3`` ALSO returns the per-data-qutrit realized levels
        ``k_bar`` (a ``(N, n_data)`` uint8 array in ``shotset.diag['terminal_levels']``); ``soft``
        ALSO returns the per-data-qutrit IQ ``z`` (a ``(N, n_data, 2)`` float64 array in
        ``shotset.diag['terminal_iq']``) drawn via ``soft_model.draw_iq``. In ALL modes the packed
        buffer (the HARD syndrome record + the logical flip) is byte-identical (L-soft-8): the
        within-cycle path is untouched and the level path's logical flip equals ⑦'s in
        distribution (hard-2-via-level == F1; L-soft-1). ``soft`` requires ``soft_model`` (a
        :class:`~qec_twin.forward.scalable.soft_readout.SoftReadoutModel`).

        PER-ROUND LEAK (P2-ii; prereg ``p2_conjunction_wiring_prereg.md`` §1 API pin).
        ``leak_slices=None`` (default) is TODAY's static arm — the spec-built ``exp(L/4)`` slice
        drives every round; the PACKED record + terminal side channels are byte-identical to the
        pre-P2-ii carrier (gate P2-ii (a); the header gains the provenance fields below). Else a
        length-``R`` sequence of per-round ``(n_kraus, 3, 3)`` slice tables: round ``r``'s LEAK
        ops sample from ``leak_slices[r]``. Each table is CPTP-ASSERTED at entry
        (``SvSampler.cptp_residual < CPTP_TOL`` — the C1 discipline: the carrier never trusts
        caller tables). Building the tables FROM the Θ fan-out (``theta_wg(t)``/``g_seep(t)``)
        is the CALLER's job — the carrier stays a data consumer. The CSR marshal is
        content-independent for leak (``op_uid=0``), so marshalling is unchanged;
        ``marsh.leak_kraus`` is not consumed by this arm (``_run_trajectory`` takes its leak
        argument explicitly). Header provenance: ``leak_slices_mode`` (``static``/``per_round``)
        + ``leak_slices_sha256`` over the stacked tables in the per-round mode.
        """
        mode = str(mode)
        if mode not in ("hard2", "hard3", "soft"):
            raise ValueError(f"sample mode must be hard2/hard3/soft (got {mode!r})")
        if mode == "soft" and soft_model is None:
            raise ValueError("mode='soft' requires soft_model (a SoftReadoutModel)")
        if not torch.cuda.is_available():
            raise RuntimeError("GPU-only contract: CUDA must be available for the MCWF-MPS forward")
        sched = self._host.parse(spec) if sched is None else sched
        if not sched.within_cycle_streams:
            raise ValueError(
                "MpsLeakageForward (within-cycle) requires sched.within_cycle_streams "
                "(a MULTI-ROUND source circuit's interior streams). Attach them via "
                "sched.with_within_cycle_streams(parse_within_cycle_streams(r10_circuit)) -- "
                "the r01-geometry + r10-interior split (model §1).")

        if str(codestate_mode) not in ("auto", "dense", "direct"):
            raise ValueError(f"codestate_mode must be auto/dense/direct (got {codestate_mode!r})")

        leak_t, _leak_ev = self._host.build_within_cycle_leak(spec)  # CPTP + compose asserted (C1)
        marsh = self._host.marshal_within_cycle(sched, leak_t, R=spec.R)

        n_data = int(marsh.n_data)
        R = int(marsh.R)

        # P2-ii per-round leak seam (prereg §1 API pin). None -> the static arm: ONE base table
        # shared by every round ([base] * R -- the identical object, so the op stream, draw order
        # and record are byte-identical to the pre-P2-ii carrier, gate P2-ii (a)). Else one
        # CPTP-asserted table per round (the carrier never trusts caller tables -- C1).
        leak_slices_sha: str | None = None
        if leak_slices is None:
            base_kraus = [leak_t[k] for k in range(leak_t.shape[0])]
            leak_by_round: list[list[torch.Tensor]] = [base_kraus] * R
        else:
            if len(leak_slices) != R:
                raise ValueError(
                    f"leak_slices must carry one (n_kraus, 3, 3) table per round: got "
                    f"{len(leak_slices)} tables for R={R}")
            tables: list[torch.Tensor] = []
            for r_i, t in enumerate(leak_slices):
                tt = torch.as_tensor(t, dtype=CDTYPE, device=self.device).contiguous()
                if tt.dim() != 3 or tt.shape[1:] != (PHYS, PHYS):
                    raise ValueError(
                        f"leak_slices[{r_i}] must be (n_kraus, 3, 3) (got {tuple(tt.shape)})")
                resid = self._host.cptp_residual(tt)
                if resid >= CPTP_TOL:
                    raise AssertionError(
                        f"leak_slices[{r_i}] CPTP residual {resid:.3e} >= {CPTP_TOL:.0e} "
                        f"(the C1 discipline: per-round tables are asserted, never trusted)")
                tables.append(tt)
            leak_by_round = [[t[k] for k in range(t.shape[0])] for t in tables]
            import hashlib
            h = hashlib.sha256()
            for t in tables:
                # shape framing: without it, differing per-round n_kraus re-chunkings of the
                # same byte stream would collide (the hash exists to disambiguate provenance).
                h.update(repr(tuple(t.shape)).encode())
                h.update(t.detach().cpu().numpy().tobytes())
            leak_slices_sha = h.hexdigest()
        # site ordering (snake or identity); bind the engine<->mps maps + logical
        # support via the public seam (attach_layout -- behavior-identical refactor).
        order = snake_order_from_coords(sched.data_coords) if snake else tuple(range(n_data))
        self.attach_layout(order, marsh.log_supp.detach().cpu().numpy().tolist())

        chi_eff = int(chi) if chi is not None else exact_chi(n_data)
        ledger = MpsTruncationLedger(chi=chi_eff)

        # codestate |m>_L. 'auto' -> the dense lift for n_data <= DENSE_CODESTATE_MAX (the
        # p7d/8e-validated d3 path, kept for regression safety) and the DIRECT MPS construction
        # above it (d5=25 / d7=49 cannot be built densely); 'dense'/'direct' force a path (the d3
        # integration anchor forces 'direct'). The direct construction is EXACT vs the dense
        # codestate at d3 (p8), so 'auto' is observationally identical on the validated d3 path.
        use_direct = (str(codestate_mode) == "direct" or
                      (str(codestate_mode) == "auto" and n_data > DENSE_CODESTATE_MAX))
        if use_direct:
            # build the codestate EXACT (its 2^boundary bond), separate from the dynamics chi_eff —
            # the trajectory then truncates it at chi_eff like the dense path does.
            cs_chi = min(exact_chi(n_data), CODESTATE_CHI_CAP)
            codestate_mps, code_evidence = self.build_codestate_mps_direct(
                sched, spec.m, cs_chi, order, self._eng_to_mps)
        else:
            codestate, code_evidence = self._host.build_codestate(sched, spec.m)  # <S>/<L> asserted
            # CONVENTION: site-0-MSB (engine qutrit p = p-th most-significant tensor factor)
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
        # terminal side channels. ``term_bits`` (ALL modes) is the per-data-qutrit computational
        # bit (⑦'s F1 bit in hard2; bit(k_bar) on the level path) — the L-soft-1 per-qubit marginal.
        term_bits = np.zeros((N, n_data), dtype=np.uint8)
        term_levels = np.zeros((N, n_data), dtype=np.uint8) if mode in ("hard3", "soft") else None
        term_iq = np.zeros((N, n_data, 2), dtype=np.float64) if mode == "soft" else None

        for shot in range(N):
            # per-shot RNG keyed by (base_seed, shot) -- a wave-layout-independent stream
            # (the host-side analog of the kernel's per-shot Philox keying). The SAME key drives
            # all terminal modes, so the syndrome record is byte-identical across modes (L-soft-8).
            rng = np.random.default_rng((int(spec.base_seed), shot))
            bits, term, shot_disc = self._run_trajectory(
                codestate_mps, marsh, leak_by_round, gate_table, stab_supp, stab_isx, stab_len,
                log_sites_eng, log_isx, str(spec.arm).upper(), float(spec.b), b_eff,
                int(spec.m), chi_eff, n_data, R, rng, ledger,
                mode=mode, soft_model=soft_model)
            syndromes[shot, :] = np.asarray(bits, dtype=np.uint8)
            flips[shot] = np.uint8(term.flip)
            term_bits[shot, :] = np.asarray(term.bits, dtype=np.uint8)
            if term_levels is not None:
                term_levels[shot, :] = np.asarray(term.levels, dtype=np.uint8)
            if term_iq is not None:
                term_iq[shot, :, :] = term.iq.detach().cpu().numpy()
            ledger.record_shot_total(shot_disc)

        packed = self._host.pack_shots(syndromes, flips)
        # the dense backend's header (byte-identical ShotSet); marshal_schedule gives the
        # MarshalledSchedule the header reader expects (gate-CSR view + logical support).
        marsh_lumped = self._host.marshal_schedule(sched, R=spec.R)
        header = self._host.build_header(spec, marsh_lumped, sched)
        header["backend"] = "mps_mcwf/quimb"
        # P2-ii provenance: which leak arm produced this record (+ a content hash per-round).
        header["leak_slices_mode"] = "static" if leak_slices is None else "per_round"
        if leak_slices_sha is not None:
            header["leak_slices_sha256"] = leak_slices_sha
        header["mps_chi"] = int(chi_eff)
        header["mps_chi_exact_grade"] = int(exact_chi(n_data))
        header["mps_snake_order"] = list(order)
        header["mps_truncation_ledger"] = ledger.report()
        header["codestate_check"] = code_evidence
        # D2 terminal-readout mode provenance. The packed buffer is byte-identical across modes;
        # hard3/soft carry the per-data-qutrit level / IQ side channels in shotset.diag.
        header["terminal_mode"] = mode
        if mode in ("hard3", "soft"):
            header["terminal_levels_shape"] = [int(N), int(n_data)]
        if mode == "soft":
            header["terminal_iq_shape"] = [int(N), int(n_data), 2]
            header["soft_model"] = soft_model.realized()  # the grounded geometry + round-trip cert

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

        diag: dict[str, Any] = {"mps_truncation": ledger.report(), "terminal_mode": mode,
                                "terminal_bits": term_bits}  # (N, n_data) uint8 per-qubit bit (all modes)
        if term_levels is not None:
            diag["terminal_levels"] = term_levels       # (N, n_data) uint8, engine order
        if term_iq is not None:
            diag["terminal_iq"] = term_iq               # (N, n_data, 2) float64, engine order
        shotset = ShotSet(
            header=header,
            path=out_path,
            header_path=header_path,
            n_shots=N,
            syndrome_bits_per_shot=bits_per_shot,
            diag=diag,
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
        # CONVENTION: site-0-MSB (engine qutrit p = p-th most-significant tensor factor)
        # -- to_dense() re-emits row-major over the SITE order; the permute below maps
        # site axes back to engine axes, restoring the engine site-0-MSB vector.
        dense_snake = torch.as_tensor(mps.to_dense(), dtype=CDTYPE, device=self.device).reshape(
            [PHYS] * sched.n_data)
        # invert the snake permutation: engine axis e sits at snake site order.index(e).
        inv = [order.index(e) for e in range(sched.n_data)]
        return dense_snake.permute(*inv).contiguous().reshape(-1)

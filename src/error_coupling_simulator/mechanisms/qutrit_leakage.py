"""Wood--Gambetta qutrit leakage channels and specified noise processes.

The physical channel acts on ``{|0>, |1>, |2>}`` through coherent
``|1><->|2>`` exchange, dissipative seepage ``|2>->|1>``, and optional heating
``|1>->|2>``.  This module owns the NumPy superoperator/Kraus algebra, its Torch
carrier conversion, Wood--Gambetta diagnostics, leaked-readout map, and neutral
``QutritLeakageNoiseProcess`` factories.  Declared parameters and diagnostics are
evaluator-only truth; emitted records do not expose them.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np
import torch

from ..numerics import NUMERICAL_ZERO

#: Torch dtype/device for the engine-native qutrit Kraus tensors (GPU only;
#: no CPU fallback in the model-compute path). Resolved at
#: build time so the default tracks the engine's device policy.
QUTRIT_CDTYPE = torch.complex128
QUTRIT_DEVICE = "cuda"


# --------------------------------------------------------------------------- #
# Declared design constants and swept ranges.                                  #
# --------------------------------------------------------------------------- #
# The leakage CHANNEL is the WG ``exp(Lindbladian)`` map parameterized by the
# physical ``(theta, g_seep, g_heat)``; the FIELD-STANDARD Wood-Gambetta rates
# ``(WG_L1, WG_L2)`` (1704.03081 Eq.2) are DIAGNOSTICS of that channel, not pinned
# inputs. The bands below are the registered §2.2 target regimes the channel siting
# must land in (the channel parameters are SWEPT, not a single magic default).

#: Per-cycle WG leakage rate ``WG_L1`` band (Miao 2211.04728 ~5e-3/cycle). The GO
#: Current certification targets WG_L1 = 1e-3 and 5e-3;
#: ``solve_theta_for_wg_l1`` finds the
#: coherent-exchange ``theta`` that hits a target WG_L1 (with C_L>0).
WG_L1_REGIME = (1.0e-3, 5.0e-3)
#: Per-cycle WG seepage rate ``WG_L2`` band (thermal-like ``L2/L1 ~ 20-50``; McEwen
#: 2102.06131 gamma_up ~0.1% / gamma_down ~8-9%/round, no-reset). Set by ``g_seep``.
WG_L2_REGIME = (5.0e-2, 1.0e-1)

#: Coherent ``|1><->|2>`` exchange strengths ``theta`` SWEPT across the registered
#: regime (documented sweep set, NOT a single pinned magic constant). These land WG_L1
#: at ~1e-3..5e-3 (``WG_L1 ~ (1/2) sin^2(theta)``): theta=0 is the incoherent-ablation
#: anchor (C_L=0), theta>0 carries C_L>0 (the non-Pauli signal). Use
#: ``solve_theta_for_wg_l1`` to hit an exact target WG_L1.
THETA_SWEEP = (0.0, 0.045, 0.07, 0.10)
#: Dissipative seepage rates ``g_seep`` SWEPT across the WG_L2 regime (jump ``|1><2|``,
#: |2>->|1>). g_seep ~ 0.05..0.10 lands WG_L2 in ``WG_L2_REGIME``.
G_SEEP_SWEEP = (0.05, 0.09, 0.10)
#: Incoherent heating rates ``g_heat`` SWEPT for the matched-WG_L1 ablation (jump
#: ``|2><1|``, |1>->|2>, C_L=0). g_heat=0 is the default (no heating); g_heat>0 with
#: theta=0 is the incoherent-leakage limit used to isolate the coherent contribution.
G_HEAT_SWEEP = (0.0, 0.005)

#: First-pass central siting (a documented mid-band point, NOT pinned magic constants;
#: the GO gate sweeps THETA_SWEEP x G_SEEP_SWEEP). theta=0.07 -> WG_L1 ~ 2.4e-3 (in the
#: Miao band, C_L>0); g_seep=0.09 -> WG_L2 ~ 9e-2 (in the McEwen band).
THETA_DEFAULT = 0.07
G_SEEP_DEFAULT = 0.09
G_HEAT_DEFAULT = 0.0

#: Leaked-ancilla READOUT-MAP bias ``b = P(|2> reads "1"-like)`` -- ``(c)``-class
#: SWEPT NUISANCE, NOT a pinned magic constant (current process contract:
#: "Leaked-ancilla readout map"). A data qutrit found in |2> during a stabilizer
#: measurement is read by the 2-outcome POVM ``F1 = |1><1| + b|2><2|``,
#: ``F0 = |0><0| + (1-b)|2><2|`` (``F0 + F1 = I``). Only the DIRECTION is grounded:
#: the |2> level sits ENERGETICALLY ABOVE |1>, so the dispersive IQ discriminator
#: places it predominantly in the EXCITED (|1>-like, bit=1) region -- a leaked
#: measure qubit "reads predominantly |1>-like", i.e. ``b > 0.5`` (Miao 2211.04728;
#: McEwen 2102.06131, leaked states discriminate as excited). The MAGNITUDE is NOT
#: pinned -- any single value (e.g. 0.9) would be an invented toy constant -- so we
#: SWEEP ``b in [0.5, 1.0]`` and report the R=1 floor as a BRACKET
#: ``[LER*(b=0.5), LER*(b=1.0)]``, never a point estimate. ``b`` is REQUIRED input
#: to every process/map factory (no silent default). The |2> population on a support
#: is ``O(leakage rate) ~ 5e-3`` so the floor is expected weakly sensitive to ``b``
#: at R=1 (a tight bracket -> leaked-readout immaterial at R=1; a wide bracket is a
#: finding -> ground ``b`` from the device IQ POVM). It is a gating nuisance,
#: never a premise.
#: The registered sweep interval and the discrete grid the harness brackets over.
LEAKED_READOUT_BIAS_INTERVAL = (0.5, 1.0)
LEAKED_READOUT_BIAS_SWEEP = (0.5, 0.75, 1.0)


# --------------------------------------------------------------------------- #
# Wood--Gambetta qutrit channel algebra.                                      #
# --------------------------------------------------------------------------- #
_QUTRIT_KETS = {level: np.eye(3, dtype=np.complex128)[level] for level in range(3)}


def _qutrit_op(output_level: int, input_level: int) -> np.ndarray:
    """Return ``|output_level><input_level|`` in the qutrit basis."""

    return np.outer(
        _QUTRIT_KETS[int(output_level)],
        _QUTRIT_KETS[int(input_level)].conj(),
    )


def _lindbladian_super(
    hamiltonian: np.ndarray,
    jumps: list[np.ndarray],
) -> np.ndarray:
    """Column-stacking GKSL generator for a finite-dimensional channel."""

    dim = int(hamiltonian.shape[0])
    eye = np.eye(dim, dtype=np.complex128)
    generator = -1j * (
        np.kron(eye, hamiltonian) - np.kron(hamiltonian.T, eye)
    )
    for jump in jumps:
        jump_dagger_jump = jump.conj().T @ jump
        generator += np.kron(jump.conj(), jump) - 0.5 * (
            np.kron(eye, jump_dagger_jump)
            + np.kron(jump_dagger_jump.T, eye)
        )
    return generator


def _apply_super(superop: np.ndarray, rho: np.ndarray) -> np.ndarray:
    """Apply a column-stacking superoperator to ``rho``."""

    dim = int(rho.shape[0])
    return (superop @ rho.reshape(-1, order="F")).reshape(dim, dim, order="F")


def leakage_channel_super(
    theta: float,
    g_seep: float,
    g_heat: float = 0.0,
    *,
    t: float = 1.0,
) -> np.ndarray:
    """Wood--Gambetta qutrit leakage channel ``exp(L t)``.

    ``theta`` drives coherent ``|1><->|2>`` exchange. ``g_seep`` and ``g_heat``
    are the non-negative rates of the jumps ``|1><2|`` and ``|2><1|``.
    """

    import scipy.linalg as _sla

    theta_value = float(theta)
    seepage_rate = float(g_seep)
    heating_rate = float(g_heat)
    duration = float(t)
    if seepage_rate < 0.0 or heating_rate < 0.0:
        raise ValueError("qutrit seepage and heating rates must be non-negative")
    if duration < 0.0:
        raise ValueError("qutrit leakage duration must be non-negative")

    hamiltonian = theta_value * (_qutrit_op(1, 2) + _qutrit_op(2, 1))
    jumps: list[np.ndarray] = []
    if seepage_rate > 0.0:
        jumps.append(math.sqrt(seepage_rate) * _qutrit_op(1, 2))
    if heating_rate > 0.0:
        jumps.append(math.sqrt(heating_rate) * _qutrit_op(2, 1))
    return _sla.expm(_lindbladian_super(hamiltonian, jumps) * duration)


def _super_to_kraus(
    superop: np.ndarray,
    *,
    tol: float = NUMERICAL_ZERO,
) -> list[np.ndarray]:
    """Choi-factorize a three-level column-stacking superoperator."""

    array = np.asarray(superop, dtype=np.complex128)
    if array.shape != (9, 9):
        raise ValueError(f"qutrit superoperator must have shape (9, 9), got {array.shape}")
    choi = np.zeros((9, 9), dtype=np.complex128)
    for input_row in range(3):
        for input_col in range(3):
            basis_op = _qutrit_op(input_row, input_col)
            choi += np.kron(_apply_super(array, basis_op), basis_op)
    choi = 0.5 * (choi + choi.conj().T)
    eigvals, eigvecs = np.linalg.eigh(choi)
    if float(np.min(eigvals)) < -float(tol):
        raise ValueError("qutrit channel Choi matrix is not positive semidefinite")
    return [
        np.sqrt(float(eigval)) * eigvecs[:, index].reshape(3, 3, order="C")
        for index, eigval in enumerate(eigvals)
        if float(eigval) > float(tol)
    ]


def leakage_kraus(
    theta: float,
    g_seep: float,
    g_heat: float = 0.0,
) -> list[np.ndarray]:
    """Kraus representation of :func:`leakage_channel_super`."""

    return _super_to_kraus(
        leakage_channel_super(float(theta), float(g_seep), float(g_heat))
    )


# --------------------------------------------------------------------------- #
# Wood-Gambetta rate diagnostics + theta calibration ((c)-class; evaluator).    #
# --------------------------------------------------------------------------- #
#: Projectors for the WG rates (1704.03081 Eq.2). Computational subspace {|0>,|1>}
#: (d1=2); leaked subspace {|2>} (d2=1).
_PI1 = np.diag([1.0, 1.0, 0.0]).astype(np.complex128)
_PI2 = np.diag([0.0, 0.0, 1.0]).astype(np.complex128)
#: ``|1>`` ket reused by ``coherence_of_leakage`` (basis ``{|0>,|1>,|2>}``).
_QUTRIT_KETS1 = np.eye(3, dtype=np.complex128)[1]


def wg_rates(theta: float, g_seep: float, g_heat: float = 0.0) -> tuple[float, float]:
    """Field-standard Wood-Gambetta leakage/seepage rates of the leakage channel (Eq.2).

    ``WG_L1 = (1/d1) Tr[Π2 E(Π1)]`` (d1=2; leakage out of ``{|0>,|1>}``) and
    ``WG_L2 = (1/d2) Tr[Π1 E(Π2)]`` (d2=1; seepage back), evaluated on the channel
    ``E = exp(L t)`` for ``(theta, g_seep, g_heat)``. These are EVALUATOR/audit
    diagnostics of the channel, not emitted-record inputs. (``Π1`` here is the full
    computational projector, the unnormalized Eq.2 form; the ``1/d1`` average over
    ``X_1`` input states is supplied by the explicit ``/2``.)
    """
    superop = leakage_channel_super(float(theta), float(g_seep), float(g_heat))
    l1 = float(np.real(np.trace(_PI2 @ _apply_super(superop, _PI1))) / 2.0)
    l2 = float(np.real(np.trace(_PI1 @ _apply_super(superop, _PI2))) / 1.0)
    return l1, l2


def coherence_of_leakage(theta: float, g_seep: float, g_heat: float = 0.0) -> float:
    """Wood-Gambetta coherence-of-leakage ``C_L = ||P_C(rho)||_1`` (WG 1704.03081 Eq.31).

    The trace-norm of the off-diagonal ``X_1``/``X_2`` block of ``E(|1><1|)``,
    ``P_C(rho) = Pi1 rho Pi2 + Pi2 rho Pi1`` (Eq.30) -- the field-standard non-Pauli
    coherence signal. For the unitary model this equals ``|sin(2*theta)|`` (WG Eq.59 is
    ``|sin t|`` with ``t = 2*theta`` here, since ``H = theta(|1><2|+|2><1|)`` vs WG's
    ``(1/2)(...)``), i.e. **2x the bare ``|rho[1,2]|``** -- the proper metric, NOT the
    off-diagonal magnitude (a 2x slip caught + fixed 2026-06-20, validated against Eq.59 in
    an independent closed-form check). ``> 0`` iff the channel
    carries coherent leakage: ``theta>0`` -> ``C_L>0``; the incoherent limit
    (``theta=0``, any ``g_seep``/``g_heat``) -> ``C_L=0``.
    """
    superop = leakage_channel_super(float(theta), float(g_seep), float(g_heat))
    out = _apply_super(superop, np.outer(_QUTRIT_KETS1, _QUTRIT_KETS1.conj()))
    pc = _PI1 @ out @ _PI2 + _PI2 @ out @ _PI1  # off-diagonal block P_C(rho), WG Eq.30
    return float(np.sum(np.linalg.svd(pc, compute_uv=False)))  # ||P_C||_1 = sum of singular values


def solve_theta_for_wg_l1(
    target_wg_l1: float,
    *,
    g_seep: float = G_SEEP_DEFAULT,
    g_heat: float = 0.0,
    tol: float = 1e-10,
    max_iter: int = 100,
) -> float:
    """Find the coherent-exchange ``theta`` whose WG channel has ``WG_L1 == target``.

    The coherent ``|1><->|2>`` exchange gives ``WG_L1 ~ (1/2) sin^2(theta)`` to leading
    order (WG Eq.58); the dissipative ``g_seep``/``g_heat`` perturb it, so this refines
    a monotone bisection on the EXACT channel rate ``wg_rates(theta, g_seep, g_heat)[0]``
    (no closed-form inversion). The bracket starts at the analytic seed
    ``theta0 = arcsin(sqrt(2 target))`` and widens to ``[0, pi/2]`` (WG_L1 is monotone
    increasing in ``theta`` on ``[0, pi/2]``). Sets the process's WG_L1 to a registered
    Miao/McEwen target (e.g. 1e-3, 5e-3) with C_L>0 -- the channel parameter ``theta`` is
    NOT a pinned magic constant; it is solved for the registered rate.
    """
    target = float(target_wg_l1)
    if target <= NUMERICAL_ZERO:
        return 0.0
    if not 0.0 < target < 0.5:
        raise ValueError(f"target WG_L1 must lie in (0, 0.5) for a |1><->|2> exchange (got {target})")
    lo, hi = 0.0, 0.5 * math.pi
    f_hi = wg_rates(hi, g_seep, g_heat)[0]
    if f_hi < target:
        raise ValueError(f"target WG_L1={target} unreachable for g_seep={g_seep}, g_heat={g_heat} (max {f_hi})")
    for _ in range(int(max_iter)):
        mid = 0.5 * (lo + hi)
        f_mid = wg_rates(mid, g_seep, g_heat)[0]
        if abs(f_mid - target) <= tol:
            return float(mid)
        if f_mid < target:
            lo = mid
        else:
            hi = mid
    return float(0.5 * (lo + hi))


# --------------------------------------------------------------------------- #
# Leaked-ancilla readout map.                                                  #
# --------------------------------------------------------------------------- #
def leaked_readout_probabilities(b: float) -> dict[int, float]:
    """The swept-``b``, parameterized leaked-readout assignment (NOT a coin flip).

    ``b = P(|2> reads "1"-like) in [0, 1]`` is a REQUIRED SWEPT NUISANCE --
    there is no default magic constant; the caller picks ``b`` from the
    registered sweep ``LEAKED_READOUT_BIAS_SWEEP`` (or the interval
    ``LEAKED_READOUT_BIAS_INTERVAL``) and reports the floor as a bracket. Returns the
    deterministic map ``data-qutrit-level -> P(syndrome bit = 1)`` that records the
    2-outcome readout POVM ``F1 = |1><1| + b|2><2|``, ``F0 = |0><0| + (1-b)|2><2|``
    (``F0 + F1 = I``):

      level |0> -> bit 1 with prob 0.0   (ground reads |0>-like; structural)
      level |1> -> bit 1 with prob 1.0   (excited reads |1>-like; structural)
      level |2> -> bit 1 with prob ``b`` (LEAKED: biased |1>-like for ``b > 0.5``, §2.2)

    The |0>/|1> entries are the exact computational-subspace readout (structural 0/1);
    only the leaked |2> row carries the ``(c)``-class swept bias. The engine
    (``QutritDM.project_stabilizer`` / ``syndrome_distribution``) consumes ``b``
    directly and forms the diagonal syndrome-bit POVM ``E_s`` from these per-level
    weights, so the joint syndrome distribution stays a well-defined POVM trace and
    remains exact given ``b``.
    """
    bval = float(b)
    if not math.isfinite(bval) or not 0.0 <= bval <= 1.0:
        raise ValueError(f"leaked-readout bias b must be a probability in [0,1] (got {bval})")
    return {0: 0.0, 1: 1.0, 2: bval}


def leaked_readout_manifest(b: float) -> dict[str, Any]:
    """Evaluator/audit record for the leaked-readout probabilities at swept bias ``b``."""
    return {
        "leaked_readout_bias_b": float(b),
        "leaked_bit1_prob": leaked_readout_probabilities(b)[2],
        "ground_bit1_prob": 0.0,
        "excited_bit1_prob": 1.0,
        "epistemic_class": "c",
        "readout_role": "swept_nuisance",
        "swept": True,
        "sweep_interval": LEAKED_READOUT_BIAS_INTERVAL,
        "sweep_grid": LEAKED_READOUT_BIAS_SWEEP,
        "direction_grounded": "b>0.5 (|2> reads |1>-like)",
        "source": "Miao 2211.04728 / McEwen 2102.06131 (leaked reads predominantly |1>-like)",
        "magnitude_pinned": False,
        "is_coin_flip": False,
    }


# --------------------------------------------------------------------------- #
# Engine-native qutrit Kraus (torch CUDA) from the NumPy channel algebra.       #
# --------------------------------------------------------------------------- #
def leakage_kraus_torch(
    theta: float,
    g_seep: float,
    g_heat: float = 0.0,
    *,
    device: str | torch.device = QUTRIT_DEVICE,
    dtype: torch.dtype = QUTRIT_CDTYPE,
) -> list[torch.Tensor]:
    """The :func:`leakage_kraus` channel as engine-
    native torch CUDA complex128 tensors (the contract's channel data format).

    Single source of truth for the algebra: it wraps the numpy WG ``leakage_kraus``
    (the same CPTP family the ``check_wg_leakage_channel.py`` channel-level qutip oracle
    validates) and only changes the carrier (numpy -> torch CUDA). No re-derivation. The
    Kraus count is the channel rank (2..5), which the engine's ``apply_channel`` consumes
    as an arbitrary-length Kraus list.
    """
    return [
        torch.as_tensor(k, dtype=dtype, device=device)
        for k in leakage_kraus(float(theta), float(g_seep), float(g_heat))
    ]


# --------------------------------------------------------------------------- #
# Specified qutrit leakage process.                                            #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class QutritLeakageNoiseProcess:
    """One evaluator-only qutrit leakage process arm.

    ``field`` is ``(t, site) -> list[(3,3) torch CUDA Kraus]`` (the per-data-qutrit
    leakage channel injected each cycle ``t`` at data site ``site``).
    ``leaked_readout`` is the swept-``b`` leaked-readout map (``data-level ->
    P(bit=1)``, with the ``|2>`` row = the swept bias ``b``).
    ``params`` records the declared ground-truth constants -- EVALUATOR/AUDIT-SIDE
    ONLY (isolation contract): never part of the emitted record payload.
    """

    name: str
    field: Callable
    leaked_readout: dict[int, float]
    params: dict[str, Any] = field(default_factory=dict)


def _const_field(kraus: list[torch.Tensor]) -> Callable:
    """A time/site-constant per-qubit leakage field."""
    return lambda t, site: kraus


def _heterogeneous_field(kraus_per_site: list[list[torch.Tensor]]) -> Callable:
    """A per-site (still time-constant) leakage field for heterogeneous rates."""
    return lambda t, site: kraus_per_site[int(site)]


def _leakage_audit(theta: float, g_seep: float, g_heat: float) -> dict[str, Any]:
    """Evaluator-side WG diagnostics for one ``(theta, g_seep, g_heat)`` channel."""
    wg_l1, wg_l2 = wg_rates(float(theta), float(g_seep), float(g_heat))
    return {
        "theta": float(theta),
        "g_seep": float(g_seep),
        "g_heat": float(g_heat),
        "WG_L1": wg_l1,
        "WG_L2": wg_l2,
        "WG_L2_over_L1": wg_l2 / wg_l1 if wg_l1 > 0.0 else float("inf"),
        "C_L": coherence_of_leakage(float(theta), float(g_seep), float(g_heat)),
        "coherent": bool(float(theta) > 0.0),
    }


def qutrit_leakage_process(
    *,
    b: float,
    theta: float = THETA_DEFAULT,
    g_seep: float = G_SEEP_DEFAULT,
    g_heat: float = G_HEAT_DEFAULT,
    n_data: int = 9,
    device: str | torch.device = QUTRIT_DEVICE,
) -> QutritLeakageNoiseProcess:
    """Homogeneous per-data-qutrit WG leakage process for d3 XZZX (9 data).

    Injects the SAME Wood-Gambetta leakage channel
    ``leakage_kraus_torch(theta, g_seep, g_heat)`` on every data qutrit each cycle
    as a coherent ``|1><->|2>`` exchange (``theta``, carrying ``C_L>0``) plus
    dissipative seepage (``g_seep``,
    WG_L2) and optional incoherent heating (``g_heat``, ``C_L=0``). ``b`` is
    REQUIRED -- no magic-constant default; pick it from ``LEAKED_READOUT_BIAS_SWEEP``
    and bracket the floor over it. The ``(theta, g_seep, g_heat)`` are SWEPT design
    constants (``THETA_SWEEP`` x ``G_SEEP_SWEEP`` x ``G_HEAT_SWEEP``); the channel's WG
    rates land in ``WG_L1_REGIME`` / ``WG_L2_REGIME`` (use ``solve_theta_for_wg_l1``
    to hit an exact target WG_L1, for example 1e-3 or 5e-3). The WG rates + ``C_L``
    are recorded in ``params`` (evaluator-side).
    """
    kraus = leakage_kraus_torch(theta, g_seep, g_heat, device=device)
    audit = _leakage_audit(theta, g_seep, g_heat)
    return QutritLeakageNoiseProcess(
        name=(
            f"qutrit-wg-leakage(theta={float(theta):.3g},g_seep={float(g_seep):.3g},"
            f"g_heat={float(g_heat):.3g},b={float(b):.3g})"
        ),
        field=_const_field(kraus),
        leaked_readout=leaked_readout_probabilities(b),
        params={
            **audit,
            "n_data": int(n_data),
            "homogeneous": True,
            "WG_L1_regime": WG_L1_REGIME,
            "WG_L2_regime": WG_L2_REGIME,
            **leaked_readout_manifest(b),
        },
    )


def qutrit_leakage_process_heterogeneous(
    rates: list[tuple[float, float, float]] | list[tuple[float, float]],
    *,
    b: float,
    device: str | torch.device = QUTRIT_DEVICE,
) -> QutritLeakageNoiseProcess:
    """Heterogeneous qutrit leakage process: ``rates[site] = (theta, g_seep[, g_heat])``.

    Each data qutrit gets its OWN registered WG channel parameters (still time-constant;
    no edge). A 2-tuple ``(theta, g_seep)`` is accepted with ``g_heat`` defaulting to 0.
    This is the heterogeneous arm for site-varying device leakage. ``b`` (the
    swept leaked-readout bias is REQUIRED
    -- no magic-constant default. Every per-site parameter must land its WG rate in / near
    the declared bands (not enforced here; an evaluator run manifest declares
    the chosen values). The per-site WG rates + ``C_L`` are recorded in ``params``.
    """
    norm_rates: list[tuple[float, float, float]] = [
        (float(r[0]), float(r[1]), float(r[2]) if len(r) > 2 else 0.0) for r in rates
    ]
    kraus_per_site = [
        leakage_kraus_torch(theta, g_seep, g_heat, device=device)
        for (theta, g_seep, g_heat) in norm_rates
    ]
    return QutritLeakageNoiseProcess(
        name=f"qutrit-wg-leakage-heterogeneous(n={len(norm_rates)},b={float(b):.3g})",
        field=_heterogeneous_field(kraus_per_site),
        leaked_readout=leaked_readout_probabilities(b),
        params={
            "rates": [(theta, g_seep, g_heat) for (theta, g_seep, g_heat) in norm_rates],
            "per_site_audit": [_leakage_audit(theta, g_seep, g_heat) for (theta, g_seep, g_heat) in norm_rates],
            "n_data": len(norm_rates),
            "homogeneous": False,
            "WG_L1_regime": WG_L1_REGIME,
            "WG_L2_regime": WG_L2_REGIME,
            **leaked_readout_manifest(b),
        },
    )

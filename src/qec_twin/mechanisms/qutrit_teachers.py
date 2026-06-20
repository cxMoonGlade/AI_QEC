from __future__ import annotations

"""Phase-1 exact-qutrit leakage TEACHER (EVALUATOR-ONLY counterfactual ground truth).

The controlled-teacher arm of the Phase-1 SIM-ONLY non-Pauli teacher-learner
program (architecture A; pre-registration
``docs/nonpauli_teacher/phase1_qutrit_leakage_registration.md``, interface
``docs/nonpauli_teacher/phase1_build_contract.md``). This module injects a KNOWN
leakage mechanism ``(theta, g_seep, g_heat)`` into the exact 9-data-qutrit d3 XZZX
density-matrix engine and supplies the leaked-ancilla readout map. It is the qutrit
analog of ``mechanisms/teachers.py`` / ``mechanisms/seam_teachers.py``.

Object (registration §0): an exact 3-level teacher for d3 XZZX that injects
per-data-qutrit Wood-Gambetta leakage on the basis ``{|0>,|1>,|2>}`` -- a COHERENT
``|1><->|2>`` exchange (strength ``theta``, carrying ``C_L>0``, the non-Pauli signal)
plus optional dissipative seepage ``|2>->|1>`` (rate ``g_seep``, WG_L2) and incoherent
heating ``|1>->|2>`` (rate ``g_heat``, ``C_L=0``) -- and a swept-``b`` leaked-readout
map (``b = P(|2> reads "1"-like)``, the §2.2 nuisance — NOT pinned).

The leakage channel was UPGRADED (2026-06-20) from the prior ``leakage_kraus(l1, l2)``
incoherent toy: that channel generated zero ``C_L`` (the program is premised on the
coherent non-Pauli signal) and its rate was 2x off the WG definition. The faithful
mechanism is now ``forward.channels.leakage_kraus(theta, g_seep, g_heat)`` (the exact
``exp(Lindbladian)`` channel); the WG rates ``(WG_L1, WG_L2)`` are DIAGNOSTICS of the
channel, not pinned inputs, and ``theta`` is found for a target WG_L1 by
``calibrate_theta_for_wg_l1`` (grounded to Miao ~5e-3 / McEwen L2).

Isolation contract (``docs/teacher_learner.md``; registration §0, binding): the
teacher's channels, its ``(theta, g_seep, g_heat)`` / WG rates, mechanism IDs, AND the
leaked-readout bias are evaluator-only counterfactual ground truth. The learner
consumes observations only -- ``(context, syndrome s, logical m)`` -- never the
teacher's parameters. Scoring is evaluator-side. ``QutritLeakageTeacher.params`` is
the audit/evaluator surface; it is never a learner input.

Data format (contract): a Kraus channel is a ``list`` of ``(3,3)`` torch CUDA
complex128 tensors, CPTP ``Σ Kᵢ†Kᵢ = I`` to <=1e-12 -- the d3 engine's native
format (``forward/exact/qutrit_dm.QutritDM.apply_channel`` consumes it; it accepts an
arbitrary-rank Kraus list, so the WG channel's rank-2..5 output is fine). The
underlying 3x3 leakage Kraus algebra lives in ``forward.channels.leakage_kraus``
(numpy, the house ``channels.py`` style); this module lifts it to torch CUDA so
Agents A/C consume the engine-native tensors.

Epistemic classes (registration §2):
  - the leakage Kraus family + its CPTP-ness + the channel-level qutip oracle
    agreement are ``(a)``-class (exact operator identities, verified in
    ``outputs/teacher_prereg/check_wg_leakage_channel.py``);
  - the per-qubit channel parameters ``(theta, g_seep, g_heat)`` and the WG rate bands
    (§2.2) are ``(c)``-class registered design constants (near-threshold siting; SWEPT,
    NOT fitted), used for go/no-go gating only;
  - the leaked-readout bias ``b = P(|2> reads "1"-like)`` (§2.2) is a ``(c)``-class
    SWEPT NUISANCE over ``[0.5, 1.0]`` — NOT a pinned magic constant. The R=1 floor
    is reported as a BRACKET over ``b`` (``LEAKED_READOUT_BIAS_SWEEP``); only the
    DIRECTION ``b > 0.5`` is device-grounded (``|2>`` sits above ``|1>`` in the IQ
    plane), the magnitude is unknown, so ``b`` is required input, never defaulted to
    an invented value such as 0.9.
"""

import math
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np
import torch

from qec_twin.forward.channels import (
    leakage_channel_super,
    leakage_kraus,
)
from qec_twin.numerics import NUMERICAL_ZERO

#: Torch dtype/device for the engine-native qutrit Kraus tensors (GPU only;
#: registration §1.6 -- no CPU fallback in the model-compute path). Resolved at
#: build time so the default tracks the engine's device policy.
QUTRIT_CDTYPE = torch.complex128
QUTRIT_DEVICE = "cuda"


# --------------------------------------------------------------------------- #
# Registered design constants ((c)-class; registration §2.2, frozen).          #
# --------------------------------------------------------------------------- #
# The leakage CHANNEL is the WG ``exp(Lindbladian)`` map parameterized by the
# physical ``(theta, g_seep, g_heat)``; the FIELD-STANDARD Wood-Gambetta rates
# ``(WG_L1, WG_L2)`` (1704.03081 Eq.2) are DIAGNOSTICS of that channel, not pinned
# inputs. The bands below are the registered §2.2 target regimes the channel siting
# must land in (the channel parameters are SWEPT, not a single magic default).

#: Per-cycle WG leakage rate ``WG_L1`` band (Miao 2211.04728 ~5e-3/cycle). The GO
#: gate (P5) targets WG_L1 = 1e-3 and 5e-3; ``calibrate_theta_for_wg_l1`` finds the
#: coherent-exchange ``theta`` that hits a target WG_L1 (with C_L>0).
WG_L1_REGIME = (1.0e-3, 5.0e-3)
#: Per-cycle WG seepage rate ``WG_L2`` band (thermal-like ``L2/L1 ~ 20-50``; McEwen
#: 2102.06131 gamma_up ~0.1% / gamma_down ~8-9%/round, no-reset). Set by ``g_seep``.
WG_L2_REGIME = (5.0e-2, 1.0e-1)

#: Coherent ``|1><->|2>`` exchange strengths ``theta`` SWEPT across the registered
#: regime (documented sweep set, NOT a single pinned magic constant). These land WG_L1
#: at ~1e-3..5e-3 (``WG_L1 ~ (1/2) sin^2(theta)``): theta=0 is the incoherent-ablation
#: anchor (C_L=0), theta>0 carries C_L>0 (the non-Pauli signal). Use
#: ``calibrate_theta_for_wg_l1`` to hit an exact target WG_L1.
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
#: SWEPT NUISANCE, NOT a pinned magic constant (registration §2.2; contract
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
#: to every teacher/map factory (no silent default). The |2> population on a support
#: is ``O(leakage rate) ~ 5e-3`` so the floor is expected weakly sensitive to ``b``
#: at R=1 (a tight bracket -> leaked-readout immaterial at R=1; a wide bracket is a
#: finding -> ground ``b`` from the device IQ POVM, Phase-3). It is a gating nuisance,
#: never a premise.
#: The registered sweep interval and the discrete grid the harness brackets over.
LEAKED_READOUT_BIAS_INTERVAL = (0.5, 1.0)
LEAKED_READOUT_BIAS_SWEEP = (0.5, 0.75, 1.0)


# --------------------------------------------------------------------------- #
# Wood-Gambetta rate diagnostics + theta calibration ((c)-class; evaluator).    #
# --------------------------------------------------------------------------- #
#: Projectors for the WG rates (1704.03081 Eq.2). Computational subspace {|0>,|1>}
#: (d1=2); leaked subspace {|2>} (d2=1).
_PI1 = np.diag([1.0, 1.0, 0.0]).astype(np.complex128)
_PI2 = np.diag([0.0, 0.0, 1.0]).astype(np.complex128)
#: ``|1>`` ket reused by ``coherence_of_leakage`` (basis ``{|0>,|1>,|2>}``).
_QUTRIT_KETS1 = np.eye(3, dtype=np.complex128)[1]


def _apply_super_np(superop: np.ndarray, rho: np.ndarray) -> np.ndarray:
    """``E(rho)`` for a column-stacking (Fortran-order vec) superoperator."""
    dim = rho.shape[0]
    return (superop @ rho.reshape(-1, order="F")).reshape(dim, dim, order="F")


def wg_rates(theta: float, g_seep: float, g_heat: float = 0.0) -> tuple[float, float]:
    """Field-standard Wood-Gambetta leakage/seepage rates of the leakage channel (Eq.2).

    ``WG_L1 = (1/d1) Tr[Π2 E(Π1)]`` (d1=2; leakage out of ``{|0>,|1>}``) and
    ``WG_L2 = (1/d2) Tr[Π1 E(Π2)]`` (d2=1; seepage back), evaluated on the channel
    ``E = exp(L t)`` for ``(theta, g_seep, g_heat)``. These are EVALUATOR/audit
    diagnostics of the channel, not learner inputs. (``Π1`` here is the full
    computational projector, the unnormalized Eq.2 form; the ``1/d1`` average over
    ``X_1`` input states is supplied by the explicit ``/2``.)
    """
    superop = leakage_channel_super(float(theta), float(g_seep), float(g_heat))
    l1 = float(np.real(np.trace(_PI2 @ _apply_super_np(superop, _PI1))) / 2.0)
    l2 = float(np.real(np.trace(_PI1 @ _apply_super_np(superop, _PI2))) / 1.0)
    return l1, l2


def coherence_of_leakage(theta: float, g_seep: float, g_heat: float = 0.0) -> float:
    """Wood-Gambetta coherence-of-leakage ``C_L = ||P_C(rho)||_1`` (WG 1704.03081 Eq.31).

    The trace-norm of the off-diagonal ``X_1``/``X_2`` block of ``E(|1><1|)``,
    ``P_C(rho) = Pi1 rho Pi2 + Pi2 rho Pi1`` (Eq.30) -- the field-standard non-Pauli
    coherence signal. For the unitary model this equals ``|sin(2*theta)|`` (WG Eq.59 is
    ``|sin t|`` with ``t = 2*theta`` here, since ``H = theta(|1><2|+|2><1|)`` vs WG's
    ``(1/2)(...)``), i.e. **2x the bare ``|rho[1,2]|``** -- the proper metric, NOT the
    off-diagonal magnitude (a 2x slip caught + fixed 2026-06-20, validated against Eq.59 in
    ``outputs/teacher_prereg/wg_closed_form_validation.py``). ``> 0`` iff the channel
    carries coherent leakage: ``theta>0`` -> ``C_L>0``; the incoherent limit
    (``theta=0``, any ``g_seep``/``g_heat``) -> ``C_L=0``.
    """
    superop = leakage_channel_super(float(theta), float(g_seep), float(g_heat))
    out = _apply_super_np(superop, np.outer(_QUTRIT_KETS1, _QUTRIT_KETS1.conj()))
    pc = _PI1 @ out @ _PI2 + _PI2 @ out @ _PI1  # off-diagonal block P_C(rho), WG Eq.30
    return float(np.sum(np.linalg.svd(pc, compute_uv=False)))  # ||P_C||_1 = sum of singular values


def calibrate_theta_for_wg_l1(
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
    increasing in ``theta`` on ``[0, pi/2]``). Grounds the teacher's WG_L1 to a registered
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
# Leaked-ancilla readout map (Agent B supplies; Agents A/C consume).           #
# --------------------------------------------------------------------------- #
def leaked_map(b: float) -> dict[int, float]:
    """The swept-``b``, parameterized leaked-readout assignment (NOT a coin flip).

    ``b = P(|2> reads "1"-like) in [0, 1]`` is a REQUIRED SWEPT NUISANCE (registration
    §2.2) -- there is no default magic constant; the caller picks ``b`` from the
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
    if not 0.0 <= bval <= 1.0:
        raise ValueError(f"leaked-readout bias b must be a probability in [0,1] (got {bval})")
    return {0: 0.0, 1: 1.0, 2: bval}


def leaked_map_params(b: float) -> dict[str, Any]:
    """Evaluator/audit record for the leaked-readout map at swept bias ``b`` ((c)-class)."""
    return {
        "leaked_readout_bias_b": float(b),
        "leaked_bit1_prob": leaked_map(b)[2],
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
# Engine-native qutrit Kraus (torch CUDA) from the channels.py numpy algebra.   #
# --------------------------------------------------------------------------- #
def leakage_kraus_torch(
    theta: float,
    g_seep: float,
    g_heat: float = 0.0,
    *,
    device: str | torch.device = QUTRIT_DEVICE,
    dtype: torch.dtype = QUTRIT_CDTYPE,
) -> list[torch.Tensor]:
    """The ``forward.channels.leakage_kraus(theta, g_seep, g_heat)`` Kraus as engine-
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
# The equal-treatment teacher object (mirrors mechanisms/seam_teachers.py).     #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class QutritLeakageTeacher:
    """One evaluator-only qutrit leakage teacher arm.

    ``field`` is ``(t, site) -> list[(3,3) torch CUDA Kraus]`` (the per-data-qutrit
    leakage channel injected each cycle ``t`` at data site ``site``). ``edge_field``
    is ``None`` in the Phase-1 CP/Markovian core (per-qubit stochastic leakage has
    no 2-qutrit edge; coherent transport is the deferred Phase-1b extension,
    registration §2.4) -- the slot is kept for the contract's
    ``(t, (i, j)) -> Kraus | None`` shape so the transport teacher drops in later.
    ``leaked_readout`` is the swept-``b`` leaked-readout map (``data-level ->
    P(bit=1)``, with the ``|2>`` row = the swept bias ``b``).
    ``params`` records the declared ground-truth constants -- EVALUATOR/AUDIT-SIDE
    ONLY (isolation contract): never a learner input.
    """

    name: str
    field: Callable
    edge_field: Callable | None
    leaked_readout: dict[int, float]
    params: dict[str, Any] = field(default_factory=dict)


def _const_field(kraus: list[torch.Tensor]) -> Callable:
    """A time/site-constant per-qubit leakage field (homogeneous teacher)."""
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


def qutrit_leakage_teacher(
    *,
    b: float,
    theta: float = THETA_DEFAULT,
    g_seep: float = G_SEEP_DEFAULT,
    g_heat: float = G_HEAT_DEFAULT,
    n_data: int = 9,
    device: str | torch.device = QUTRIT_DEVICE,
) -> QutritLeakageTeacher:
    """Homogeneous per-data-qutrit WG leakage teacher ``(theta, g_seep, g_heat)`` for d3 XZZX (9 data).

    Injects the SAME Wood-Gambetta leakage channel
    ``leakage_kraus_torch(theta, g_seep, g_heat)`` on every data qutrit each cycle
    (first-pass per-qubit leakage, registration §2.2): a COHERENT ``|1><->|2>``
    exchange (``theta``, carrying ``C_L>0``) plus dissipative seepage (``g_seep``,
    WG_L2) and optional incoherent heating (``g_heat``, ``C_L=0``). No edge
    (CP/Markovian core). ``b`` (the swept leaked-readout bias, registration §2.2) is
    REQUIRED -- no magic-constant default; pick it from ``LEAKED_READOUT_BIAS_SWEEP``
    and bracket the floor over it. The ``(theta, g_seep, g_heat)`` are SWEPT design
    constants (``THETA_SWEEP`` x ``G_SEEP_SWEEP`` x ``G_HEAT_SWEEP``); the channel's WG
    rates land in ``WG_L1_REGIME`` / ``WG_L2_REGIME`` (use ``calibrate_theta_for_wg_l1``
    to hit an exact target WG_L1, e.g. the GO-gate 1e-3 / 5e-3). The WG rates + ``C_L``
    are recorded in ``params`` (evaluator-side).
    """
    kraus = leakage_kraus_torch(theta, g_seep, g_heat, device=device)
    audit = _leakage_audit(theta, g_seep, g_heat)
    return QutritLeakageTeacher(
        name=(
            f"qutrit-wg-leakage(theta={float(theta):.3g},g_seep={float(g_seep):.3g},"
            f"g_heat={float(g_heat):.3g},b={float(b):.3g})"
        ),
        field=_const_field(kraus),
        edge_field=None,
        leaked_readout=leaked_map(b),
        params={
            **audit,
            "n_data": int(n_data),
            "homogeneous": True,
            "WG_L1_regime": WG_L1_REGIME,
            "WG_L2_regime": WG_L2_REGIME,
            "edge_present": False,
            "transport_deferred": True,  # registration §2.4 (Phase-1b)
            **leaked_map_params(b),
        },
    )


def qutrit_leakage_teacher_heterogeneous(
    rates: list[tuple[float, float, float]] | list[tuple[float, float]],
    *,
    b: float,
    device: str | torch.device = QUTRIT_DEVICE,
) -> QutritLeakageTeacher:
    """Per-data-qutrit heterogeneous WG leakage teacher: ``rates[site] = (theta, g_seep[, g_heat])``.

    Each data qutrit gets its OWN registered WG channel parameters (still time-constant;
    no edge). A 2-tuple ``(theta, g_seep)`` is accepted with ``g_heat`` defaulting to 0.
    Mirrors ``teachers.mixed_mechanism_field`` -- the heterogeneous arm for site-varying
    device leakage. ``b`` (the swept leaked-readout bias, registration §2.2) is REQUIRED
    -- no magic-constant default. Every per-site parameter must land its WG rate in / near
    the registered §2.2 bands (not enforced here; an evaluator pre-registration declares
    the chosen values). The per-site WG rates + ``C_L`` are recorded in ``params``.
    """
    norm_rates: list[tuple[float, float, float]] = [
        (float(r[0]), float(r[1]), float(r[2]) if len(r) > 2 else 0.0) for r in rates
    ]
    kraus_per_site = [
        leakage_kraus_torch(theta, g_seep, g_heat, device=device)
        for (theta, g_seep, g_heat) in norm_rates
    ]
    return QutritLeakageTeacher(
        name=f"qutrit-wg-leakage-heterogeneous(n={len(norm_rates)},b={float(b):.3g})",
        field=_heterogeneous_field(kraus_per_site),
        edge_field=None,
        leaked_readout=leaked_map(b),
        params={
            "rates": [(theta, g_seep, g_heat) for (theta, g_seep, g_heat) in norm_rates],
            "per_site_audit": [_leakage_audit(theta, g_seep, g_heat) for (theta, g_seep, g_heat) in norm_rates],
            "n_data": len(norm_rates),
            "homogeneous": False,
            "WG_L1_regime": WG_L1_REGIME,
            "WG_L2_regime": WG_L2_REGIME,
            "edge_present": False,
            "transport_deferred": True,
            **leaked_map_params(b),
        },
    )

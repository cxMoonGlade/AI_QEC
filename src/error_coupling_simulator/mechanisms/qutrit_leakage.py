"""Qutrit exchange, seepage, and heating channels and specified processes.

The declared model channel acts on ``{|0>, |1>, |2>}`` through coherent
``|1><->|2>`` exchange, dissipative seepage ``|2>->|1>``, and optional heating
``|1>->|2>``.  This module owns the NumPy superoperator/Kraus algebra, its Torch
carrier conversion, subspace-transition diagnostics, leaked-readout map, and
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
# The leakage channel is the declared ``exp(Lindbladian)`` map parameterized by
# ``(theta, g_seep, g_heat)``. Computational-to-leaked and
# leaked-to-computational subspace rates are diagnostics, not measured inputs.
# The ranges below are project targets for sensitivity studies.

#: Project computational-to-leaked subspace-rate targets. The upper value has
#: approximate cross-observable
#: scale context from Miao 2211.04728, but is not a measurement of this project channel.
LEAKAGE_RATE_TARGETS = (1.0e-3, 5.0e-3)
#: Project leaked-to-computational subspace-rate targets. McEwen 2102.06131
#: provides cross-protocol scale context, not a fitted interval for this channel.
SEEPAGE_RATE_TARGETS = (5.0e-2, 1.0e-1)

#: Coherent ``|1><->|2>`` exchange strengths swept across the project range.
#: These land the leakage-rate diagnostic near 1e-3..5e-3 for the declared
#: default dissipative coordinates. ``theta=0`` is the exchange-off anchor. Use
#: ``solve_exchange_angle_for_leakage_rate`` to hit an exact reachable target.
THETA_SWEEP = (0.0, 0.045, 0.07, 0.10)
#: Dissipative seepage rates ``g_seep`` swept across the project target range
#: (jump ``|1><2|``, |2>->|1>).
G_SEEP_SWEEP = (0.05, 0.09, 0.10)
#: Incoherent heating rates ``g_heat`` swept for a matched-leakage-rate ablation
#: (jump ``|2><1|``, |1>->|2>). ``g_heat=0`` is the no-heating anchor.
G_HEAT_SWEEP = (0.0, 0.005)

#: Convenience center for the project sweep.
THETA_DEFAULT = 0.07
G_SEEP_DEFAULT = 0.09
G_HEAT_DEFAULT = 0.0

#: Leaked-ancilla readout-map bias ``b = P(|2> reads "1"-like)`` is a swept project
#: nuisance, not a measured device parameter. A data qutrit found in |2> during a stabilizer
#: measurement is read by the 2-outcome POVM ``F1 = |1><1| + b|2><2|``,
#: ``F0 = |0><0| + (1-b)|2><2|`` (``F0 + F1 = I``). The chosen interval
#: ``b in [0.5, 1.0]`` is a project-design sensitivity range. Neither its direction
#: nor any point value is inferred from the cited leakage experiments. ``b`` is a
#: required factory input so the assumption cannot be hidden.
#: The registered sweep interval and the discrete grid the harness brackets over.
LEAKED_READOUT_BIAS_INTERVAL = (0.5, 1.0)
LEAKED_READOUT_BIAS_SWEEP = (0.5, 0.75, 1.0)


# --------------------------------------------------------------------------- #
# Qutrit exchange/seepage/heating channel algebra.                            #
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
    """Declared qutrit exchange/seepage/heating channel ``exp(L t)``.

    ``theta`` drives coherent ``|1><->|2>`` exchange. ``g_seep`` and ``g_heat``
    are the non-negative rates of the jumps ``|1><2|`` and ``|2><1|``.
    """

    import scipy.linalg as _sla

    theta_value = float(theta)
    seepage_rate = float(g_seep)
    heating_rate = float(g_heat)
    duration = float(t)
    if not all(math.isfinite(value) for value in (theta_value, seepage_rate, heating_rate, duration)):
        raise ValueError("qutrit leakage parameters and duration must be finite")
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
# Subspace-transition diagnostics and project-target solver.                  #
# --------------------------------------------------------------------------- #
#: Computational subspace ``{|0>,|1>}`` and leaked subspace ``{|2>}``
#: projectors used by the source-backed transition-rate definitions.
_PI1 = np.diag([1.0, 1.0, 0.0]).astype(np.complex128)
_PI2 = np.diag([0.0, 0.0, 1.0]).astype(np.complex128)
#: Explicit fixed input for ``level1_output_leakage_coherence``.
_QUTRIT_KETS1 = np.eye(3, dtype=np.complex128)[1]


def leakage_seepage_rates(
    theta: float,
    g_seep: float,
    g_heat: float = 0.0,
) -> tuple[float, float]:
    """Return computational-to-leaked and leaked-to-computational rates.

    The definitions are ``Tr[Π_leak E(Π_comp)] / d_comp`` and
    ``Tr[Π_comp E(Π_leak)] / d_leak`` with dimensions two and one. They are
    evaluator diagnostics of the declared channel, not emitted-record inputs.
    Source: Phys. Rev. A 97, 032306 (2018), Eq. (2).
    """
    superop = leakage_channel_super(float(theta), float(g_seep), float(g_heat))
    l1 = float(np.real(np.trace(_PI2 @ _apply_super(superop, _PI1))) / 2.0)
    l2 = float(np.real(np.trace(_PI1 @ _apply_super(superop, _PI2))) / 1.0)
    return l1, l2


def level1_output_leakage_coherence(
    theta: float,
    g_seep: float,
    g_heat: float = 0.0,
) -> float:
    """Trace norm of the cross-subspace block of ``E(|1><1|)``.

    This is the state functional ``||Π_comp rho Π_leak + Π_leak rho Π_comp||_1``
    evaluated only after the explicit fixed input ``|1><1|``. It is not a Haar
    channel average and must not be interpreted as an iff test for a coherent
    physical cause. In the exchange-only model it is ``|sin(2 theta)|`` and
    therefore has a node at ``theta=pi/2`` despite the nonzero exchange generator.
    Source: Phys. Rev. A 97, 032306 (2018), Eqs. (30)-(34), (57)-(58), and (61).
    """
    superop = leakage_channel_super(float(theta), float(g_seep), float(g_heat))
    out = _apply_super(superop, np.outer(_QUTRIT_KETS1, _QUTRIT_KETS1.conj()))
    pc = _PI1 @ out @ _PI2 + _PI2 @ out @ _PI1
    return float(np.sum(np.linalg.svd(pc, compute_uv=False)))


def solve_exchange_angle_for_leakage_rate(
    target_leakage_rate: float,
    *,
    g_seep: float = G_SEEP_DEFAULT,
    g_heat: float = 0.0,
    tol: float = 1e-10,
    max_iter: int = 100,
    bracket_samples: int = 256,
) -> float:
    """Find ``theta`` whose declared channel has the requested leakage rate.

    The rate need not be monotone once dissipation is present. The solver scans
    ``[0, pi/2]`` for the first residual sign change and then performs a
    direction-independent bisection inside that explicit bracket. Returning
    zero is allowed only for exact equality with the computed ``theta=0`` rate.
    A zero target never uses numerical tolerance to turn positive probability
    into a structural zero. Failure to bracket or meet ``tol`` raises instead
    of returning an unverified midpoint. This is a project-channel coordinate,
    not calibration.
    """
    target = float(target_leakage_rate)
    tolerance = float(tol)
    if not math.isfinite(target) or not 0.0 <= target <= 0.5:
        raise ValueError(
            "target leakage rate must be finite and lie in [0, 0.5] "
            f"(got {target_leakage_rate!r})"
        )
    if not math.isfinite(tolerance) or tolerance <= 0.0:
        raise ValueError(f"tol must be finite and positive (got {tol!r})")
    try:
        iterations = int(max_iter)
    except (TypeError, ValueError, OverflowError):
        raise ValueError(
            f"max_iter must be a positive integer (got {max_iter!r})"
        ) from None
    if isinstance(max_iter, bool) or iterations <= 0 or iterations != max_iter:
        raise ValueError(f"max_iter must be a positive integer (got {max_iter!r})")
    try:
        samples = int(bracket_samples)
    except (TypeError, ValueError, OverflowError):
        raise ValueError(
            f"bracket_samples must be an integer >= 2 (got {bracket_samples!r})"
        ) from None
    if (
        isinstance(bracket_samples, bool)
        or samples < 2
        or samples != bracket_samples
    ):
        raise ValueError(
            f"bracket_samples must be an integer >= 2 (got {bracket_samples!r})"
        )

    def rate(angle: float) -> float:
        return leakage_seepage_rates(angle, g_seep, g_heat)[0]

    def converged(value: float) -> bool:
        if target == 0.0:
            return value == 0.0
        return abs(value - target) <= min(tolerance, 0.5 * target)

    grid = np.linspace(0.0, 0.5 * math.pi, samples + 1, dtype=np.float64)
    lo = float(grid[0])
    f_lo = rate(lo)
    if target == f_lo:
        return lo
    residual_lo = f_lo - target
    sampled_min = f_lo
    sampled_max = f_lo
    bracket: tuple[float, float, float] | None = None
    for raw_hi in grid[1:]:
        hi = float(raw_hi)
        f_hi = rate(hi)
        sampled_min = min(sampled_min, f_hi)
        sampled_max = max(sampled_max, f_hi)
        if converged(f_hi):
            return hi
        residual_hi = f_hi - target
        if residual_lo * residual_hi < 0.0:
            bracket = (lo, hi, residual_lo)
            break
        lo, residual_lo = hi, residual_hi
    if bracket is None:
        raise ValueError(
            f"target leakage rate {target} was not bracketed by the {samples}-sample "
            f"scan on theta in [0, pi/2] for g_seep={g_seep}, g_heat={g_heat}; "
            f"sampled range was "
            f"[{sampled_min}, {sampled_max}]"
        )
    lo, hi, residual_lo = bracket
    for _ in range(iterations):
        mid = 0.5 * (lo + hi)
        f_mid = rate(mid)
        if converged(f_mid):
            return float(mid)
        residual_mid = f_mid - target
        if residual_lo * residual_mid < 0.0:
            hi = mid
        else:
            lo, residual_lo = mid, residual_mid
    candidate = float(0.5 * (lo + hi))
    candidate_rate = rate(candidate)
    residual = abs(candidate_rate - target)
    if converged(candidate_rate):
        return candidate
    raise RuntimeError(
        f"exchange-angle solver did not reach tolerance {tolerance} after "
        f"{iterations} iterations (residual {residual})"
    )


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
      level |2> -> bit 1 with prob ``b`` (by definition, ``b > 0.5`` is more
                                      |1>-like than |0>-like)

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
        "direction_provenance": "project-design",
        "literature_supports_binary_map": False,
        "source": None,
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

    Single source of truth for the algebra: it wraps NumPy ``leakage_kraus`` and
    only changes the carrier (NumPy -> Torch CUDA). No re-derivation. The
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
    """Evaluator-side diagnostics for one ``(theta, g_seep, g_heat)`` channel."""
    leakage_rate, seepage_rate = leakage_seepage_rates(
        float(theta), float(g_seep), float(g_heat)
    )
    return {
        "theta": float(theta),
        "g_seep": float(g_seep),
        "g_heat": float(g_heat),
        "leakage_rate": leakage_rate,
        "seepage_rate": seepage_rate,
        "level1_output_leakage_coherence": level1_output_leakage_coherence(
            float(theta), float(g_seep), float(g_heat)
        ),
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
    """Homogeneous per-data-qutrit leakage process for d3 XZZX (9 data).

    Injects the same declared channel on every data qutrit each cycle: coherent
    ``|1><->|2>`` exchange, dissipative seepage, and optional heating. ``b`` is
    REQUIRED -- no magic-constant default; pick it from ``LEAKED_READOUT_BIAS_SWEEP``
    and bracket the floor over it. The ``(theta, g_seep, g_heat)`` are SWEPT design
    constants. Subspace rates and the explicitly fixed-input coherence diagnostic
    are recorded in evaluator-only ``params``.
    """
    kraus = leakage_kraus_torch(theta, g_seep, g_heat, device=device)
    audit = _leakage_audit(theta, g_seep, g_heat)
    return QutritLeakageNoiseProcess(
        name=(
            f"qutrit-leakage(theta={float(theta):.3g},g_seep={float(g_seep):.3g},"
            f"g_heat={float(g_heat):.3g},b={float(b):.3g})"
        ),
        field=_const_field(kraus),
        leaked_readout=leaked_readout_probabilities(b),
        params={
            **audit,
            "n_data": int(n_data),
            "homogeneous": True,
            "leakage_rate_targets": LEAKAGE_RATE_TARGETS,
            "seepage_rate_targets": SEEPAGE_RATE_TARGETS,
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

    Each data qutrit gets its own registered channel parameters (still time-constant;
    no edge). A 2-tuple ``(theta, g_seep)`` is accepted with ``g_heat`` defaulting to 0.
    This is the heterogeneous arm for site-varying device leakage. ``b`` (the
    swept leaked-readout bias is REQUIRED
    -- no magic-constant default. Per-site diagnostics are recorded in ``params``.
    """
    norm_rates: list[tuple[float, float, float]] = [
        (float(r[0]), float(r[1]), float(r[2]) if len(r) > 2 else 0.0) for r in rates
    ]
    kraus_per_site = [
        leakage_kraus_torch(theta, g_seep, g_heat, device=device)
        for (theta, g_seep, g_heat) in norm_rates
    ]
    return QutritLeakageNoiseProcess(
        name=f"qutrit-leakage-heterogeneous(n={len(norm_rates)},b={float(b):.3g})",
        field=_heterogeneous_field(kraus_per_site),
        leaked_readout=leaked_readout_probabilities(b),
        params={
            "rates": [(theta, g_seep, g_heat) for (theta, g_seep, g_heat) in norm_rates],
            "per_site_audit": [_leakage_audit(theta, g_seep, g_heat) for (theta, g_seep, g_heat) in norm_rates],
            "n_data": len(norm_rates),
            "homogeneous": False,
            "leakage_rate_targets": LEAKAGE_RATE_TARGETS,
            "seepage_rate_targets": SEEPAGE_RATE_TARGETS,
            **leaked_readout_manifest(b),
        },
    )

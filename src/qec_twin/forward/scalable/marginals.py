from __future__ import annotations

"""Fit-free bunching functionals of the carrier law (seam-test registration item 6).

``R_det`` at lag ``k`` and the consecutive-triple ``T3`` are computed from a
TWO-BLOCK MARGINAL of the (stationary) carrier law -- a direct enumeration of
the registered window forward, never a fit and never a sampled estimate.

RECORD CONVENTION (declared; the D5<->K2 convention pin -- every R_k in the
seam-test registration declares its record). All functionals in this module are
**data-record-chain** functionals: the chain is the per-round measured parity
record ``r_t`` of ONE declared check ``j`` of a window, under per-round
non-selective extraction of every other check (the steady-state round map of
``forward/exact/steady_state``). The flip event is ``F_t = r_t XOR r_{t-1}``;
with the stationary flip rate ``r = P(F_t = 1)``:

    R_k = P(F_t = 1, F_{t+k} = 1) / (P(F_t = 1) P(F_{t+k} = 1))
    T3  = P(F_t = F_{t+1} = F_{t+2} = 1) / r**3

D5 exact references (evaluated by tests, never assumed): a time-constant T-B
local channel with diagonal-Markov pair ``(p01, p10)`` gives
``R_k = 1 + (R - 1) lambda1**(k-1)`` with ``lambda1 = 1 - p01 - p10`` and
``T3 = R`` exactly; a unital-diagonal field (``p01 = p10``) pins ``R_k == 1``
(the sharp T-B boundary). Mechanism ATTRIBUTION from these numbers uses lags
``k >= 2`` only (registration item 6; D5's readout-contamination rule) -- lag 1
is computed here for the exact identities but is not an attribution lag.

Construction (D3): ``F_t`` needs records ``(r_{t-1}, r_t)`` and ``F_{t+k}``
needs ``(r_{t+k-1}, r_{t+k})`` -- four enumerated records (16 branches on one
check) joined by ``k - 2`` non-selective rounds, CONSTANT in lag; ``k = 1``
shares the middle record (three enumerated records). The pre-block state is the
stationary state of the round map (the M3 burn-in machinery, fixed-point pin
``<= 1e-9`` reused as registered)."""

import torch

from qec_twin.forward.exact.circuit_sim import (
    apply_channel_local,
    dephase_parity_sweep,
    measure_parity_enumerate,
)

# Stationary-state machinery shared with the validated M3 path (private import,
# deliberate: the burn-in/doubling schedule must be THE registered one).
from qec_twin.forward.exact.steady_state import (
    DEFAULT_BURN_IN,
    DEFAULT_FP_TOL,
    DEFAULT_MAX_BURN_IN,
    _burn_in,
)
from qec_twin.forward.cptp_channel import RDTYPE
from qec_twin.numerics import NUMERICAL_ZERO


def _channel_layer(rho: torch.Tensor, channel_field, t: int, n: int) -> torch.Tensor:
    for i in range(n):
        kraus = channel_field(t, i)
        if kraus is not None:
            rho = apply_channel_local(rho, kraus, [i], n)
    return rho


def _enumerated_records(
    channel_field,
    *,
    distance: int,
    check: int,
    schedule: list[bool],
    burn_in: int,
    max_burn_in: int,
    fp_tol: float,
    device: str | torch.device,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Run the stationary round map; per round, record check ``check`` selectively
    where ``schedule[t]`` is True and discard otherwise. Every other check is
    always non-selective (the full parity-dephase sweep; re-dephasing the
    just-projected check is exact). Returns ``(records, probs)`` with ``records``
    ``(B, sum(schedule))`` int64."""
    n = int(distance)
    j = int(check)
    rho, _, total = _burn_in(
        channel_field, n, burn_in=burn_in, max_burn_in=max_burn_in, tol=fp_tol, device=device
    )
    outcomes = torch.zeros((1, 0), dtype=RDTYPE, device=device)
    t = total
    for selective in schedule:
        rho = _channel_layer(rho, channel_field, t, n)
        if selective:
            rho, outcomes = measure_parity_enumerate(rho, outcomes, j, j + 1, n)
        rho = dephase_parity_sweep(rho, n)
        t += 1
    probs = torch.diagonal(rho, dim1=-2, dim2=-1).real.sum(-1)
    return outcomes.round().long(), probs


def r_det_lag(
    channel_field,
    *,
    distance: int,
    check: int = 0,
    lag: int = 2,
    burn_in: int = DEFAULT_BURN_IN,
    max_burn_in: int = DEFAULT_MAX_BURN_IN,
    fp_tol: float = DEFAULT_FP_TOL,
    device: str | torch.device = "cpu",
) -> dict[str, float]:
    """``R_k`` of the carrier law from the two-block marginal (no fit).

    ``lag >= 1``; the registered attribution convention is ``k >= 2`` (module
    docstring -- the value is exact either way, the convention is carried with
    the number)."""
    k = int(lag)
    if k < 1:
        raise ValueError(f"lag must be >= 1 (got {k})")
    if k == 1:
        schedule = [True, True, True]  # r_a, r_b, r_c: F1 = b^a, F2 = c^b
    else:
        schedule = [True, True] + [False] * (k - 2) + [True, True]
    records, probs = _enumerated_records(
        channel_field,
        distance=distance,
        check=check,
        schedule=schedule,
        burn_in=burn_in,
        max_burn_in=max_burn_in,
        fp_tol=fp_tol,
        device=device,
    )
    f1 = records[:, 1] ^ records[:, 0]
    f2 = records[:, -1] ^ records[:, -2]
    p_f1 = probs[f1 == 1].sum()
    p_f2 = probs[f2 == 1].sum()
    p_joint = probs[(f1 == 1) & (f2 == 1)].sum()
    r_k = float(p_joint / (p_f1 * p_f2).clamp_min(NUMERICAL_ZERO))
    return {
        "R_k": r_k,
        "lag": float(k),
        "flip_rate": float(p_f1),
        "flip_rate_late": float(p_f2),
        "p_joint": float(p_joint),
        "record": "data-record-chain",
    }


def t3_triple(
    channel_field,
    *,
    distance: int,
    check: int = 0,
    burn_in: int = DEFAULT_BURN_IN,
    max_burn_in: int = DEFAULT_MAX_BURN_IN,
    fp_tol: float = DEFAULT_FP_TOL,
    device: str | torch.device = "cpu",
) -> dict[str, float]:
    """The consecutive-triple ``T3 = P(FFF) / r**3`` (no fit; T-B predicts
    ``T3 = R`` exactly -- the registered tie-breaker, Skew_pi(f) >= 0 scope
    carried by the registration, not re-derived here)."""
    records, probs = _enumerated_records(
        channel_field,
        distance=distance,
        check=check,
        schedule=[True, True, True, True],  # r_0..r_3 -> F1, F2, F3
        burn_in=burn_in,
        max_burn_in=max_burn_in,
        fp_tol=fp_tol,
        device=device,
    )
    flips = records[:, 1:] ^ records[:, :-1]  # (B, 3)
    p_f = probs[flips[:, 0] == 1].sum()
    p_all = probs[(flips == 1).all(dim=1)].sum()
    t3 = float(p_all / (p_f**3).clamp_min(NUMERICAL_ZERO))
    return {
        "T3": t3,
        "flip_rate": float(p_f),
        "p_triple": float(p_all),
        "record": "data-record-chain",
    }

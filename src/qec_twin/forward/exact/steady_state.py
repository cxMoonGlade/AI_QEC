from __future__ import annotations

"""Exact stationary detector-block law of a rep-code window (R2-lite M3).

Pre-registration: docs/metric_results.md "2026-06-09 -- R2-lite M3" (frozen
design, Candidate A). The window forward IS a distance-5 repetition code on the
parity backend (2**5 register, no ancillas): 5 data qubits, 4 parity checks --
all four checks are the 6-site window's fully-interior detectors; the window's
two boundary checks touch exterior data and are marginalized (not modeled; the
TWO-POINT cross-cut mass was risk-audited by M2's X2 <= 4.24% -- a heuristic
go/no-go gate, NOT a residual bound: no theorem bounds the marginal-calibration
error from X2; see hardware/windows.py STATUS WARNING).

Construction (derived; the run verifies, never explores)
--------------------------------------------------------
The device's bulk detector at (site j, layer t) is the consecutive-round record
XOR ``d_{t,j} = r_{t,j} XOR r_{t-1,j}`` (rep_code.py convention, bulk rows of
``_detectors_and_observable``). A 2-layer block at start ``t`` collects
``(d_t, d_{t+1})`` over the 4 checks -- a function of THREE consecutive records
``(r_{t-1}, r_t, r_{t+1})``. Deep in the bulk (t >= 80 >> the M1-P6 transient)
the pre-round state is the stationary state ``rho*`` of the round map
``Phi = (parity dephase sweep) o (channel layer)``, so the exact block law is
the law of ``(r_1 XOR r_0, r_2 XOR r_1)`` when ``rounds = 3`` extraction rounds
are enumerated from ``rho*``. Two rounds would NOT suffice: the two detector
layers need three records, and conditioning ``r_{t-1}`` on stationarity (not on
a fresh reset) is exactly what the burn-in provides. The non-selective burn-in
is exact because the record-discarded post-measurement state is
``sum_b P_b rho P_b`` (:func:`dephase_parity`); stationarity of ``rho*`` plus a
time-invariant channel field makes the law independent of ``t``, so one law
scores every disjoint block of the family.

Generally, ``rounds = R`` enumerated rounds yield ``R - 1`` detector layers and
a flattened law of size ``2**(nchecks * (R - 1))`` -- 256 for the registered
``R = 3`` at distance 5 (4096 branches, ~67 MB peak).

Burn-in init (the "mixed-state init"): the closed-form diagonal stationary
product ``rho_0 = prod_i diag(pi_i)`` with ``pi_i(1) = p01_i / (p01_i + p10_i)``
read off each channel's diagonal-Markov pair. After the dephase sweep only
diagonals and the 5-qubit "cat" coherences (|x><~x|, ~(coh)^5 ~ 1e-10) survive,
and the diagonal dynamics is EXACTLY the per-qubit product chain, whose fixed
point is this product -- so the init already solves the diagonal sector and the
``B = 40`` burn-in (doubling to ``max_burn_in`` on a residual miss) only has to
settle the cat-term tail, which is what makes the registered fixed-point pin
``||rho_B - Phi(rho_B)||_1 <= 1e-9`` reachable. (From the maximally mixed state
the slowest diagonal mode decays as ``(1 - p01 - p10)^B``, which provably
cannot reach 1e-9 within 320 rounds at device rates.)

Bit convention (pinned; identical in hardware/blocks.py, the readout
convolution, and the baselines): site ``j`` (left to right), detector layer
``l`` (0 = block start), bit index ``(R - 1) * j + l``; for the registered
2-layer block, ``pattern = sum_j (d_{t,j} + 2 * d_{t+1,j}) * 4**j``.
"""

import torch

from qec_twin.forward.cptp_channel import CDTYPE, RDTYPE
from qec_twin.forward.exact.circuit_sim import (
    apply_channel_local,
    dephase_parity_sweep,
    measure_parity_enumerate,
)
from qec_twin.numerics import NUMERICAL_ZERO

DEFAULT_BURN_IN = 40
DEFAULT_MAX_BURN_IN = 320
DEFAULT_FP_TOL = 1e-9


def diagonal_markov_pair(kraus: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """The channel's diagonal-Markov pair ``(p01, p10)`` -- the M3-recoverable object.

    ``p01 = P(0 -> 1) = sum_e |(K_e)_{1,0}|^2`` and ``p10 = P(1 -> 0)``;
    differentiable in the Kraus stack.
    """
    p01 = (kraus[:, 1, 0].abs() ** 2).sum()
    p10 = (kraus[:, 0, 1].abs() ** 2).sum()
    return p01, p10


def _stationary_diagonal_init(
    channel_field, n: int, device: str | torch.device
) -> torch.Tensor:
    """``(1, 2**n, 2**n)`` diagonal product state of the per-qubit chain fixed points."""
    weights = []
    for i in range(n):
        kraus = channel_field(0, i)
        if kraus is None:
            pi1 = torch.tensor(0.5, dtype=RDTYPE, device=device)
        else:
            p01, p10 = diagonal_markov_pair(kraus.to(device))
            pi1 = p01 / (p01 + p10).clamp_min(NUMERICAL_ZERO)
        weights.append(torch.stack([1.0 - pi1, pi1]))
    diag = weights[0]
    for w in weights[1:]:
        diag = (diag[:, None] * w[None, :]).reshape(-1)
    rho = torch.diag_embed(diag.to(CDTYPE)).unsqueeze(0)
    return rho


def _round_map(rho: torch.Tensor, channel_field, t: int, n: int) -> torch.Tensor:
    """One extraction round: per-qubit channel layer, then the dephase sweep
    (fused: one cached mask multiply, bit-exact to the sequential j-loop)."""
    for i in range(n):
        kraus = channel_field(t, i)
        if kraus is not None:
            rho = apply_channel_local(rho, kraus, [i], n)
    return dephase_parity_sweep(rho, n)


def _trace_norm(rho: torch.Tensor) -> torch.Tensor:
    return torch.linalg.matrix_norm(rho, ord="nuc").sum()


def _burn_in(
    channel_field,
    n: int,
    *,
    burn_in: int,
    max_burn_in: int,
    tol: float,
    device: str | torch.device,
    check_residual: bool = True,
) -> tuple[torch.Tensor, float, int]:
    """Burn ``rho_0`` under the round map with the registered doubling schedule.

    Applies ``burn_in`` rounds, checks ``||rho_B - Phi(rho_B)||_1`` (under
    ``no_grad`` -- diagnostic only), and doubles the total round count until the
    residual meets ``tol`` or ``max_burn_in`` is reached. Returns
    ``(rho_B, residual, rounds_used)``; the returned state carries gradients
    w.r.t. the channel parameters through every applied round and the init.

    ``check_residual=False`` runs EXACTLY ``burn_in`` rounds with no residual
    computation, no doubling and no host synchronization (no ``float()`` /
    ``item()`` anywhere on the path) -- a fixed-shape, sync-free forward for
    CUDA-graph / torch.compile capture (pin P1h). The residual slot of the
    return is ``nan`` (never computed); the state is the same computation as
    the default path whenever the default converges in exactly ``burn_in``
    rounds (identical rounds, ops and order -- the diagnostic it skips only
    inspects a detached copy).
    """
    rho = _stationary_diagonal_init(channel_field, n, device)
    if not check_residual:
        for t in range(int(burn_in)):
            rho = _round_map(rho, channel_field, t, n)
        return rho, float("nan"), int(burn_in)
    total = 0
    stage = int(burn_in)
    while True:
        for _ in range(stage):
            rho = _round_map(rho, channel_field, total, n)
            total += 1
        with torch.no_grad():
            residual = float(_trace_norm(_round_map(rho.detach(), channel_field, total, n) - rho))
        if residual <= float(tol) or total >= int(max_burn_in):
            return rho, residual, total
        stage = min(total, int(max_burn_in) - total)


def fixed_point_residual(
    channel_field,
    *,
    distance: int = 5,
    burn_in: int = DEFAULT_BURN_IN,
    max_burn_in: int = DEFAULT_MAX_BURN_IN,
    tol: float = DEFAULT_FP_TOL,
    device: str | torch.device = "cpu",
) -> tuple[float, int]:
    """The M3-P1b pin: ``||rho_B - Phi(rho_B)||_1`` after the doubling schedule.

    Returns ``(residual, rounds_used)``; the registered gate is
    ``residual <= 1e-9`` at ``B = 40`` doubling ``<= 320``.
    """
    with torch.no_grad():
        _, residual, rounds_used = _burn_in(
            channel_field,
            int(distance),
            burn_in=burn_in,
            max_burn_in=max_burn_in,
            tol=tol,
            device=device,
        )
    return residual, rounds_used


def simulate_steady_block(
    channel_field,
    *,
    distance: int = 5,
    burn_in: int = DEFAULT_BURN_IN,
    max_burn_in: int = DEFAULT_MAX_BURN_IN,
    fp_tol: float = DEFAULT_FP_TOL,
    rounds: int = 3,
    device: str | torch.device = "cpu",
    check_residual: bool = True,
) -> torch.Tensor:
    """Exact stationary joint law of the interior-detector block (flattened).

    ``channel_field`` is the rep_code-convention callable
    ``(round_t, data_index_i) -> (k, 2, 2) Kraus stack | None``; it must be
    time-invariant for the stationary construction to be meaningful (the M3
    twin class is time-shared). After the doubling burn-in (module docstring),
    ``rounds`` extraction rounds are branch-ENUMERATED
    (:func:`measure_parity_enumerate`; ``2**(nchecks * rounds)`` branches), the
    ``rounds - 1`` detector layers are formed as consecutive-round record XORs,
    and the branch probabilities are scatter-added by the pinned pattern code.
    Returns a ``(2**(nchecks * (rounds - 1)),)`` real tensor (256 for the
    registered ``distance=5, rounds=3``), differentiable w.r.t. any leaf
    parameters of the channel field; CUDA tensors auto-route through the fused
    kernel inside :func:`apply_channel_local`.

    ``check_residual=False`` makes the burn-in run exactly ``burn_in`` rounds
    with no fixed-point diagnostic, doubling, or host sync (:func:`_burn_in`;
    pin P1h) -- the law equals the default path exactly whenever the default
    converges at ``burn_in`` rounds.
    """
    n = int(distance)
    nchecks = n - 1
    r = int(rounds)
    if r < 2:
        raise ValueError(f"rounds must be >= 2 (got {r}): a block needs two detector layers' records")

    rho, _, total = _burn_in(
        channel_field, n, burn_in=burn_in, max_burn_in=max_burn_in, tol=fp_tol, device=device,
        check_residual=check_residual,
    )

    outcomes = torch.zeros((1, 0), dtype=RDTYPE, device=device)
    for t in range(r):
        for i in range(n):
            kraus = channel_field(total + t, i)
            if kraus is not None:
                rho = apply_channel_local(rho, kraus, [i], n)
        for j in range(nchecks):
            rho, outcomes = measure_parity_enumerate(rho, outcomes, j, j + 1, n)

    probs = torch.diagonal(rho, dim1=-2, dim2=-1).real.sum(-1)  # (2**(nchecks*r),)
    records = outcomes.round().long()  # (B, r * nchecks), column t * nchecks + j

    bits_per_site = r - 1
    code = torch.zeros(records.shape[0], dtype=torch.long, device=records.device)
    for j in range(nchecks):
        for layer in range(bits_per_site):
            det = records[:, (layer + 1) * nchecks + j] ^ records[:, layer * nchecks + j]
            code = code + det * (2 ** (bits_per_site * j + layer))

    law = torch.zeros(2 ** (nchecks * bits_per_site), dtype=probs.dtype, device=probs.device)
    return law.scatter_add(0, code, probs)

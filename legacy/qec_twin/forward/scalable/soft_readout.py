from __future__ import annotations

"""soft_readout -- the terminal soft-IQ emission model (D2, the soft-readout (3) phase).

THE LOAD-BEARING PHYSICS (orchestrator-fixed, ``d2_soft_emission_build_contract.md`` §1):
an IQ point ``z=(I,Q) in R^2`` is emitted from a per-level Gaussian mixture
``f^{(k)}(z) = N(z; c_k, Sigma_k)``, ``k in {0,1,2}`` (the Pattison 2107.13589 / Ali et al.
2403.00706 field-standard soft model). The hidden state per measured qubit is the
ALREADY-COLLAPSED level ``k_bar in {0,1,2}`` (the carrier's 3-outcome projective terminal
read); the emitter is the classical noisy channel that maps it to a continuous ``z``.

Geometry (contract §1, exact restatement -- implemented to the letter):
- ``|0>/|1>`` (computational) blobs: ``c_0=(+1,0)``, ``c_1=(-1,0)`` (means +-1 on the I
  discriminant axis, separation 2); ``Sigma_0=Sigma_1=sigma^2 I_2`` isotropic;
  ``sigma = 1/SNR``, ``SNR = Phi^{-1}(1-p_m)`` (the (a)-exact assignment-error<->SNR
  relation; equivalently ``p_m = 1/2 erfc(SNR/sqrt(2))``). The Q axis is pure noise for
  ``|0>/|1>`` => the I-projection is information-lossless (under symmetry, S3).
- ``|2>`` blob: ``c_2=(c_2I, c_2Q)``, ``Sigma_2=sigma_2^2 I_2``, ``sigma_2 = sigma2_scale*sigma``.
  GROUNDED knobs (``p_m, b, p22_target, sigma2_scale``); the geometry is DERIVED, never free:
    * ``c_2I`` from the anchor: the 2-state threshold at ``I=0`` (bit=0 if I>0, bit=1 if I<0)
      gives ``beta1 = P(I<0 | |2>) = Phi((0 - c_2I)/sigma_2)``; setting ``beta1 = b`` =>
      ``c_2I = -sigma_2 * Phi^{-1}(b)`` (b>0.5 => c_2I<0, the ``|1>`` side -- "``|2>`` reads 1").
    * ``|c_2Q|`` from ``p22_target``: ``P(2->2) = int_{R_2} f^{(2)}(z) dz``, where
      ``R_2 = {z : f^{(2)}(z) >= f^{(0)}(z) AND f^{(2)}(z) >= f^{(1)}(z)}`` is the 3-state ML
      decision region (uniform prior). Solved numerically (bisection on ``|c_2Q|``, P(2->2)
      by a fine 2-D quadrature) so the realized ``P(2->2) = p22_target``. ``c_2Q >= 0`` WLOG
      (the model is symmetric in Q-sign). Infeasible ``p22_target`` (> max achievable, or
      > 0.94) RAISES.

THE ANTI-TOY ROUND-TRIP CERT (``realized()``, the key deliverable): recompute ``beta1`` (from
the solved ``c_2I, sigma_2`` via ``Phi``) and ``P(2->2)`` (from the solved geometry via the SAME
decision-region integral) and report them next to the input ``(b, p22_target)`` -- the
self-check asserts they match to tol AND that ``P(2->2) <= 0.94``. This proves the ``|2>``
geometry is PINNED by the grounded knobs, not a free toy knob handing the answer
(``docs/FAITHFULNESS_PROTOCOL.md`` Rule II.6 -- underdetermined => bracket + sensitivity,
never freeze; the ``|c_2Q|`` toy-risk is exactly the #1 soft "fake headroom" pit).

PROTOCOL (binding, ``CLAUDE.md`` / contract §4): GPU-only model compute (``device='cuda'``,
no CPU fallback, no "cuda if available else cpu"); ``float64`` for the IQ. The independent
ground-truth checks (round-trip vs a from-scratch 3-Gaussian integral; the ``(2/sigma^2)|I|``
closed form) live in ``outputs/teacher_prereg/d2a_soft_readout_selfcheck.py`` -- a check vs
this module's own ``loglik`` is NOT certification (circular).
"""

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import torch

from qec_twin.numerics import NUMERICAL_ZERO

if TYPE_CHECKING:  # pragma: no cover - typing only
    from numpy.random import Generator

# --------------------------------------------------------------------------- #
# Device / dtype policy (GPU-only model compute; float64 IQ -- contract §4).   #
# --------------------------------------------------------------------------- #
DEVICE = "cuda"
RDTYPE = torch.float64

# The literature cap on correct-|2>-ID (contract §1 / D1 §3.2): a model with P(2->2) above
# this is UNPHYSICAL on a QEC device (Krinner: the |2> class ~2.4x's the assignment error;
# the literature never shows |2> trivially/perfectly separable) and is rejected.
P22_CAP = 0.94

# Quadrature defaults for the P(2->2) decision-region integral. The grid must comfortably
# cover all three blobs at the largest sigma in play; HALF is in mean-units (the |0>/|1>
# means sit at +-1), N_GRID the per-axis sample count. Defaults certified in the self-check
# (the grid-doubling convergence print + the from-scratch independent-integral agreement).
_QUAD_HALF = 12.0
_QUAD_N = 1601


def _device(device: "str | torch.device") -> torch.device:
    """Resolve the compute device -- GPU-only (no silent CPU fallback; CLAUDE.md GPU rule)."""
    dev = torch.device(device)
    if dev.type != "cuda":
        raise ValueError(
            f"soft_readout model compute is GPU-only (device={device!r}); "
            "no CPU fallback, no 'cuda if available else cpu' (CLAUDE.md)."
        )
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available -- the soft emitter is GPU-only model compute.")
    return dev


def _Phi(x: torch.Tensor) -> torch.Tensor:
    """Standard-normal CDF Phi (torch.special.ndtr) -- float64, on-device."""
    return torch.special.ndtr(x)


def _Phi_inv(p: "float | torch.Tensor", device: torch.device) -> torch.Tensor:
    """Standard-normal quantile Phi^{-1} (torch.special.ndtri) -- float64, on-device."""
    t = torch.as_tensor(p, dtype=RDTYPE, device=device)
    return torch.special.ndtri(t)


# --------------------------------------------------------------------------- #
# The IQ geometry quadrature (the ONE numerical primitive; reused by realized) #
# --------------------------------------------------------------------------- #
def _log_gaussian_2d(z: torch.Tensor, c: torch.Tensor, var: float) -> torch.Tensor:
    """log N(z; c, var*I_2) for z (...,2). Isotropic 2-D Gaussian, float64."""
    d2 = ((z - c) ** 2).sum(dim=-1)
    return -d2 / (2.0 * var) - math.log(2.0 * math.pi * var)


def _p22_on_grid(
    c2I: float, c2Q: float, var2: float, var01: float, device: torch.device,
    half: float = _QUAD_HALF, n_grid: int = _QUAD_N,
) -> float:
    """P(2->2) = int_{R_2} f^{(2)}(z) dz by a midpoint 2-D quadrature on a [-half,half]^2 grid.

    R_2 = {z : f^{(2)}(z) >= f^{(0)}(z) AND f^{(2)}(z) >= f^{(1)}(z)} -- the 3-state ML
    decision region (uniform prior). The integrand is the |2> density on the ML-region mask.
    This is the SAME method realized() uses for the round-trip recompute (contract §1).
    """
    axis = torch.linspace(-half, half, n_grid, dtype=RDTYPE, device=device)
    dz = float(axis[1] - axis[0])
    I, Q = torch.meshgrid(axis, axis, indexing="ij")
    z = torch.stack([I, Q], dim=-1)  # (n,n,2)
    c0 = torch.tensor([1.0, 0.0], dtype=RDTYPE, device=device)
    c1 = torch.tensor([-1.0, 0.0], dtype=RDTYPE, device=device)
    c2 = torch.tensor([c2I, c2Q], dtype=RDTYPE, device=device)
    lf0 = _log_gaussian_2d(z, c0, var01)
    lf1 = _log_gaussian_2d(z, c1, var01)
    lf2 = _log_gaussian_2d(z, c2, var2)
    region2 = (lf2 >= lf0) & (lf2 >= lf1)  # the |2> ML decision region (uniform prior)
    f2 = torch.exp(lf2)
    return float((f2 * region2).sum() * (dz * dz))


def _solve_c2Q(
    b: float, p22_target: float, var2: float, var01: float, c2I: float, device: torch.device,
    tol: float = 1e-9, max_iter: int = 200,
) -> tuple[float, float]:
    """Bisect on |c_2Q| >= 0 so the ML-region P(2->2) == p22_target. Returns (c2Q, p22_lo_at_0).

    P(2->2) is MONOTONE INCREASING in |c_2Q| at fixed (c_2I, sigma_2, sigma): pushing |2> off
    the discriminant axis separates it from the collinear |0>/|1> blobs, enlarging its ML
    region. We bracket [0, hi], grow hi until P(hi) >= target (or hi caps), then bisect.
    RAISES if p22_target exceeds the achievable maximum (the unphysical-separation toy guard).
    """
    p_at_0 = _p22_on_grid(c2I, 0.0, var2, var01, device)
    if p22_target <= p_at_0:
        # collinear (|c_2Q|=0) already meets/exceeds the target: the worst-for-soft endpoint.
        # Solve down toward 0 if strictly below; if target < p_at_0 the model cannot go lower
        # than the collinear value with c2Q>=0, so 0 is the closest admissible point.
        if p22_target < p_at_0 - tol:
            # target below the collinear floor: not reachable with c2Q>=0 at this (c2I,sigma_2)
            # -> the collinear endpoint IS the floor; return it (caller checks the round-trip).
            return 0.0, p_at_0
        return 0.0, p_at_0
    # grow hi until P(2->2) >= target or we exceed a sane separation (then it is infeasible).
    hi = max(1.0, abs(c2I) + math.sqrt(var2) + 1.0)
    p_hi = _p22_on_grid(c2I, hi, var2, var01, device)
    grow = 0
    while p_hi < p22_target and grow < 60:
        hi *= 1.5
        p_hi = _p22_on_grid(c2I, hi, var2, var01, device)
        grow += 1
        if hi > _QUAD_HALF - 3.0 * math.sqrt(var2):
            break
    if p_hi < p22_target - tol:
        raise ValueError(
            f"p22_target={p22_target:.4f} is INFEASIBLE: the max achievable P(2->2) at "
            f"(b={b}, sigma_2^2={var2:.4g}) is ~{p_hi:.4f} (< target). A |2> separation large "
            f"enough is unphysical / off the quadrature grid (contract §1 -- RAISE)."
        )
    lo, hi_b = 0.0, hi
    p_lo = p_at_0
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi_b)
        p_mid = _p22_on_grid(c2I, mid, var2, var01, device)
        if abs(p_mid - p22_target) < tol:
            return mid, p_at_0
        if p_mid < p22_target:
            lo, p_lo = mid, p_mid
        else:
            hi_b, p_hi = mid, p_mid
        if (hi_b - lo) < 1e-12:
            break
    return 0.5 * (lo + hi_b), p_at_0


# --------------------------------------------------------------------------- #
# The public model (the A<->B<->C contract -- d2 contract §5)                  #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class SoftReadoutModel:
    """The terminal soft-IQ emission model (contract §1/§5; A owns).

    Construct with the GROUNDED knobs ``(p_m, b, p22_target, sigma2_scale)``; the IQ geometry
    (``sigma, c0, c1, c2, sigma_2``) is SOLVED in ``__post_init__`` and pinned. ``realized()``
    is the round-trip cert (recomputed ``beta1`` / ``P(2->2)`` vs the inputs). The public API
    ``draw_iq / loglik / harden_bit / posterior`` is what B (the seam/forward) and C (the
    cert tests) build against.

    GPU-only model compute (``device='cuda'``), ``float64`` IQ.
    """

    p_m: float
    b: float
    p22_target: float
    sigma2_scale: float = 1.0
    device: str = DEVICE
    quad_half: float = _QUAD_HALF
    quad_n: int = _QUAD_N

    # solved geometry (set in __post_init__; frozen dataclass => object.__setattr__)
    sigma: float = field(init=False, default=0.0)
    sigma_2: float = field(init=False, default=0.0)
    c0: tuple = field(init=False, default=(1.0, 0.0))
    c1: tuple = field(init=False, default=(-1.0, 0.0))
    c2: tuple = field(init=False, default=(0.0, 0.0))
    _beta1_recomputed: float = field(init=False, default=0.0)
    _p22_recomputed: float = field(init=False, default=0.0)
    _p22_collinear: float = field(init=False, default=0.0)

    def __post_init__(self) -> None:
        dev = _device(self.device)
        # --- input validation (grounded-knob ranges) ---
        if not (0.0 < self.p_m < 0.5):
            raise ValueError(f"p_m must be in (0, 0.5); got {self.p_m}")
        if not (0.0 < self.b < 1.0):
            raise ValueError(f"b (leaked-readout bias) must be in (0, 1); got {self.b}")
        if not (0.0 < self.p22_target <= 1.0):
            raise ValueError(f"p22_target must be in (0, 1]; got {self.p22_target}")
        if self.p22_target > P22_CAP:
            raise ValueError(
                f"p22_target={self.p22_target} exceeds the literature cap {P22_CAP} "
                "(|2> is never trivially separable on QEC devices -- contract §1 RAISE)."
            )
        if self.sigma2_scale <= 0.0:
            raise ValueError(f"sigma2_scale must be > 0; got {self.sigma2_scale}")

        # --- |0>/|1> geometry: sigma from SNR = Phi^{-1}(1 - p_m) (the (a)-exact relation) ---
        snr = float(_Phi_inv(1.0 - self.p_m, dev))
        if snr <= 0.0:
            raise ValueError(f"degenerate SNR={snr} for p_m={self.p_m}")
        sigma = 1.0 / snr
        sigma_2 = float(self.sigma2_scale) * sigma
        var01 = sigma * sigma
        var2 = sigma_2 * sigma_2

        # --- |2> on-axis: c_2I = -sigma_2 * Phi^{-1}(b) (the anchor beta1 = b) ---
        c2I = -sigma_2 * float(_Phi_inv(self.b, dev))

        # --- |2> off-axis: solve |c_2Q| so the ML-region P(2->2) == p22_target ---
        c2Q, p22_collinear = _solve_c2Q(
            self.b, self.p22_target, var2, var01, c2I, dev,
        )

        # --- round-trip RECOMPUTE (the anti-toy cert): beta1 and P(2->2) from the SOLVED geom ---
        beta1_rt = float(_Phi(torch.as_tensor((0.0 - c2I) / sigma_2, dtype=RDTYPE, device=dev)))
        p22_rt = _p22_on_grid(c2I, c2Q, var2, var01, dev, half=self.quad_half, n_grid=self.quad_n)

        object.__setattr__(self, "sigma", sigma)
        object.__setattr__(self, "sigma_2", sigma_2)
        object.__setattr__(self, "c0", (1.0, 0.0))
        object.__setattr__(self, "c1", (-1.0, 0.0))
        object.__setattr__(self, "c2", (float(c2I), float(c2Q)))
        object.__setattr__(self, "_beta1_recomputed", beta1_rt)
        object.__setattr__(self, "_p22_recomputed", float(p22_rt))
        object.__setattr__(self, "_p22_collinear", float(p22_collinear))

    # ----------------------------------------------------------------------- #
    # tensors for the three blob means / variances (on-device, float64)        #
    # ----------------------------------------------------------------------- #
    def _means(self, dev: torch.device) -> torch.Tensor:
        """(3,2) the three blob means c_0, c_1, c_2."""
        return torch.tensor([self.c0, self.c1, self.c2], dtype=RDTYPE, device=dev)

    def _vars(self, dev: torch.device) -> torch.Tensor:
        """(3,) the three isotropic variances sigma^2, sigma^2, sigma_2^2."""
        v01 = self.sigma * self.sigma
        v2 = self.sigma_2 * self.sigma_2
        return torch.tensor([v01, v01, v2], dtype=RDTYPE, device=dev)

    # ----------------------------------------------------------------------- #
    # Public API (contract §5)                                                 #
    # ----------------------------------------------------------------------- #
    def draw_iq(self, levels: torch.Tensor, gen: "Generator") -> torch.Tensor:
        """Draw z ~ f^{(k)}(z) per element (contract §5). One 2-D isotropic normal from the
        level's blob. ``levels`` is an int tensor (...,) of k in {0,1,2}; returns (...,2) float64
        on the model device. The randomness is drawn from ``gen`` (a numpy Generator, matching
        the carrier's host-uniform-stream convention) so the draw is reproducible / seed-matched.
        """
        dev = _device(self.device)
        lev = levels.to(dev).long()
        if torch.any(lev < 0) or torch.any(lev > 2):
            raise ValueError("levels must be in {0,1,2}")
        means = self._means(dev)  # (3,2)
        stds = torch.sqrt(self._vars(dev))  # (3,)
        mu = means[lev]  # (...,2)
        sd = stds[lev].unsqueeze(-1)  # (...,1)
        # standard normal from the host generator (seed-matched, like the carrier draws),
        # then scale+shift; GPU tensor for the model-compute path.
        shape = tuple(lev.shape) + (2,)
        eps_np = gen.standard_normal(size=shape)
        eps = torch.as_tensor(eps_np, dtype=RDTYPE, device=dev)
        return mu + sd * eps

    def loglik(self, z: torch.Tensor) -> torch.Tensor:
        """log f^{(k)}(z) for k=0,1,2 (contract §5). z (...,2) -> (...,3). float64, on-device."""
        dev = _device(self.device)
        zt = z.to(dev).to(RDTYPE)
        means = self._means(dev)  # (3,2)
        var = self._vars(dev)  # (3,)
        diff = zt.unsqueeze(-2) - means  # (...,3,2)
        sq = (diff * diff).sum(dim=-1)  # (...,3)
        return -sq / (2.0 * var) - torch.log(2.0 * math.pi * var)

    def harden_bit(self, z: torch.Tensor) -> torch.Tensor:
        """The ML 2-state threshold (contract §5): bit = 0 if I>0 else 1. z (...,2) -> (...,) int.
        This recovers the carrier's hard-2 terminal (the threshold sits at I=0 by the |0>/|1>
        symmetry; |2> projects to bit=1 with probability beta1=b by the anchor)."""
        dev = _device(self.device)
        zt = z.to(dev).to(RDTYPE)
        I = zt[..., 0]
        return torch.where(I > 0.0, torch.zeros_like(I, dtype=torch.long),
                           torch.ones_like(I, dtype=torch.long))

    def posterior(self, z: torch.Tensor) -> torch.Tensor:
        """P(k|z), uniform prior (contract §5) = softmax of loglik over k. z (...,2) -> (...,3)."""
        ll = self.loglik(z)
        return torch.softmax(ll, dim=-1)

    def realized(self) -> dict:
        """The round-trip cert evidence (contract §5 / §1): the SOLVED geometry + the RECOMPUTED
        ``beta1`` (from c_2I,sigma_2 via Phi) and ``P(2->2)`` (from the solved geometry via the
        ML-region integral), to be asserted == the input ``(b, p22_target)`` in the self-check.
        ``p22_le_0p94`` is the unphysical-separation reject flag (must be True)."""
        return {
            "p_m": float(self.p_m),
            "b": float(self.b),
            "p22_target": float(self.p22_target),
            "sigma2_scale": float(self.sigma2_scale),
            "sigma": float(self.sigma),
            "sigma_2": float(self.sigma_2),
            "snr": 1.0 / float(self.sigma),
            "c0": tuple(float(x) for x in self.c0),
            "c1": tuple(float(x) for x in self.c1),
            "c2": tuple(float(x) for x in self.c2),
            "c2I": float(self.c2[0]),
            "c2Q": float(self.c2[1]),
            # the round-trip recomputed quantities (the anti-toy cert):
            "beta1": float(self._beta1_recomputed),
            "p22": float(self._p22_recomputed),
            "p22_collinear": float(self._p22_collinear),  # P(2->2) at |c_2Q|=0 (worst-for-soft)
            "p22_le_0p94": bool(self._p22_recomputed <= P22_CAP + 1e-9),
        }

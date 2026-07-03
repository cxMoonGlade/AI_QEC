#!/usr/bin/env python
r"""EXPLICIT NON-MARKOVIAN noise SOURCE layer (Builder ① deliverable — the contribution's seed).

WHAT THIS IS
------------
The explicit non-Markovian noise SOURCE carried as a dynamical degree of freedom (NOT a
non-negative Lindblad rate — that is Markovian by construction and reproduces the owned QMCtwin
class). The source is a CLASSICAL pure-dephasing process (ledger row S2a): a random-telegraph
fluctuator (RTN/TLS) and its colored 1/f sum-of-RTNs extension, with the EXACT Anderson-Kubo /
Dutta-Horn analytic anchors.

Binding contract (implement, do NOT re-derive):
  - docs/twin_validation/nonmarkovian_coupling_constraint_ledger.md  (rows C1,C2,C3,C6,C7,C8a;
    S1,S2a,S2b,S3,S4)
  - docs/twin_validation/full_error_coupling_prereg.md  §0, §5, §5.1  (RTN convention + P1-P3)
  - docs/FAITHFULNESS_PROTOCOL.md  (rules I/II/III)

CONVENTION (ledger/prereg §5.1, FIXED — do not change; the other 2 builders code against it):
  xi(t) in {+1,-1}, switching rate gamma_sw, latent autocorr  <xi(0)xi(tau)> = exp(-2*gamma_sw*|tau|).
  Qubit phase  phi(t) = v * integral_0^t xi(t') dt'   (v = the +/-v frequency shift when the TLS flips).
  Exact RTN coherence (Anderson-Kubo):
      L(t) = <exp(i*phi(t))> = exp(-gamma_sw*t) * [cosh(mu*t) + (gamma_sw/mu)*sinh(mu*t)],
      mu = sqrt(gamma_sw^2 - v^2).
    * v < gamma_sw  (mu real)      -> OVERDAMPED, monotone exponential-ish decay.
    * v > gamma_sw  (mu imaginary) -> cosh/sinh -> cos/sin -> REVIVALS (information backflow).
  Motional-narrowing (fast/weak, v << gamma_sw):  L(t) -> exp(-Gamma*t), Gamma = v^2/(2*gamma_sw).
  RTN latent autocorr (C7/C8a):  C(tau) = v^2 * exp(-2*gamma_sw*tau)   (the SCALED-by-v^2 dephasing
    autocorr; the bare +/-1 telegraph autocorr is exp(-2*gamma_sw*tau)).
  1/f (Dutta-Horn): a log-spaced sum of N RTNs has the CLOSED-FORM spectrum
      S(omega) = sum_k v_k^2 * (4*gamma_k) / ((2*gamma_k)^2 + omega^2)   (sum of Lorentzians)
    -> ~ 1/omega over the band by construction.

EPISTEMIC FRAME (METRICS.md):
  - rtn_coherence_analytic / rtn_autocorr_analytic / motional_narrowing_rate /
    sum_lorentzian_spectrum_analytic  are (a) EXACT closed forms (the only class usable as a
    premise / positive control / ground truth). S2a is exact (it IS the model).
  - the source-build choices (finite N, geometry, stationarity) are (c) design; bounded in
    nm_source_gtcheck.py and below.

DISCIPLINE (HARD CONSTRAINTS):
  - AUTHOR-only: NO torch / GPU / QuTiP / heavy runs here. Pure numpy. The orchestrator runs the
    gtcheck SERIALLY.
  - complex128 wherever complex.
  - seeds EXPLICIT (numpy Generator from an int seed); NEVER time/global RNG.
  - this module is the {E(t)} family the divisibility detector (Builder ②) + the wedge (Builder ③)
    consume; the signatures below are the STABLE INTERFACE — keep them.

OWNERSHIP: Builder ① owns ONLY nm_source.py + nm_source_gtcheck.py. Divisibility detector + wedge
are the other two builders'; do NOT touch theirs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

import numpy as np

# numerical floor (project convention; see src/qec_twin/numerics.py).
NUMERICAL_ZERO = 1e-12


# =========================================================================== #
# Parameter containers.                                                        #
# =========================================================================== #
@dataclass(frozen=True)
class RTNParams:
    """A single random-telegraph fluctuator (RTN / TLS).

    v        : the qubit angular-frequency shift (rad/ns) when the TLS flips (the +/-v coupling).
    gamma_sw : the telegraph SWITCHING rate (1/ns); latent autocorr decays as exp(-2*gamma_sw*tau).
    """

    v: float
    gamma_sw: float

    def __post_init__(self) -> None:
        assert self.v >= 0.0, "RTNParams.v must be >= 0 (amplitude)."
        assert self.gamma_sw > 0.0, "RTNParams.gamma_sw must be > 0 (switching rate)."


@dataclass(frozen=True)
class OneOverFParams:
    """A colored 1/f process as a log-spaced SUM of N RTNs (Dutta-Horn construction).

    v_list     : per-fluctuator couplings v_k (rad/ns), length N.
    gamma_list : per-fluctuator switching rates gamma_k (1/ns), length N (log-spaced for 1/f).

    For an ideal 1/f over [gamma_min, gamma_max], v_k is held constant (each Lorentzian contributes
    a 1/omega segment whose envelope sums to 1/omega across the log-spaced gamma_k); see
    make_1f_params() for the canonical log-spaced grid.
    """

    v_list: Tuple[float, ...]
    gamma_list: Tuple[float, ...]

    def __post_init__(self) -> None:
        assert len(self.v_list) == len(self.gamma_list) and len(self.v_list) >= 1, \
            "OneOverFParams: v_list and gamma_list must be equal-length, non-empty."
        assert all(g > 0.0 for g in self.gamma_list), "OneOverFParams: all gamma_k must be > 0."
        assert all(v >= 0.0 for v in self.v_list), "OneOverFParams: all v_k must be >= 0."

    @property
    def n(self) -> int:
        return len(self.v_list)

    def rtns(self) -> List[RTNParams]:
        return [RTNParams(v=float(v), gamma_sw=float(g))
                for v, g in zip(self.v_list, self.gamma_list)]


def make_1f_params(v: float, gamma_min: float, gamma_max: float, n: int) -> OneOverFParams:
    """Canonical log-spaced sum-of-RTNs for a 1/f spectrum over [gamma_min, gamma_max].

    Constant v per fluctuator + geometric (log-spaced) gamma_k is the standard Dutta-Horn /
    Bergli-Faoro-Ioffe-Galperin construction giving S(omega) ~ 1/omega between 2*gamma_min and
    2*gamma_max. n is the (c)-design fluctuator count (S1: more N -> tighter 1/f; bounded in
    the gtcheck). Returns an OneOverFParams.
    """
    assert gamma_max > gamma_min > 0.0 and n >= 2, "make_1f_params: need 0<gamma_min<gamma_max, n>=2."
    gammas = np.geomspace(float(gamma_min), float(gamma_max), int(n))
    vs = np.full(int(n), float(v), dtype=np.float64)
    return OneOverFParams(v_list=tuple(float(x) for x in vs),
                          gamma_list=tuple(float(x) for x in gammas))


# =========================================================================== #
# (a) EXACT analytic anchors — the ground truth, the only class usable as a    #
#     premise / positive control. Independent of any sampler.                  #
# =========================================================================== #
def rtn_coherence_analytic(p: RTNParams, t):
    """[C2] EXACT Anderson-Kubo RTN coherence  L(t) = <exp(i*phi(t))>.

        L(t) = exp(-gamma*t) * [cosh(mu*t) + (gamma/mu)*sinh(mu*t)],  mu = sqrt(gamma^2 - v^2),
        gamma = gamma_sw.

    Handles BOTH branches via complex mu (numpy promotes automatically):
      - v < gamma (mu real)      -> overdamped, real-valued monotone-ish decay;
      - v > gamma (mu imaginary) -> cosh/sinh become cos/sin -> REVIVALS.
    For this symmetric (zero-mean +/-v) classical-dephasing model phi is symmetric, so L(t) is real
    (the imaginary parts cancel exactly); we return the real part as a real float/array but compute
    in complex128 to keep the imaginary branch exact. Accepts scalar or array t (returns matching).
    """
    gamma = float(p.gamma_sw)
    v = float(p.v)
    t_arr = np.asarray(t, dtype=np.float64)
    # mu in complex128: real for v<gamma, imaginary for v>gamma, exactly 0 at v==gamma.
    mu = np.sqrt(np.asarray(gamma * gamma - v * v, dtype=np.complex128))
    gt = gamma * t_arr
    if np.ndim(mu) == 0 and abs(mu) < NUMERICAL_ZERO:
        # critically-damped limit v == gamma: lim_{mu->0} cosh(mu t)+(gamma/mu)sinh(mu t) = 1 + gamma t.
        val = np.exp(-gt) * (1.0 + gt)
        out = np.asarray(val, dtype=np.complex128)
    else:
        mut = mu * t_arr
        # cosh(mut) + (gamma/mu) sinh(mut), with the mu->0 limit sinh(mut)/mu -> t (avoids the
        # gamma/mu blow-up at the v==gamma critical point; that point is measure-zero on a v-sweep,
        # and the near-critical scalar is handled by the branch above).
        cosh_term = np.cosh(mut)
        mu_safe = np.where(np.abs(mu) < NUMERICAL_ZERO, 1.0, mu)
        sinh_over_mu = np.where(np.abs(mu) < NUMERICAL_ZERO, t_arr, np.sinh(mut) / mu_safe)
        out = np.exp(-gt) * (cosh_term + gamma * sinh_over_mu)
    out = np.asarray(out, dtype=np.complex128)
    # L(t) is real for this symmetric model; the imaginary residue is numerical (< 1e-12).
    real = np.real(out)
    if np.ndim(t_arr) == 0:
        return float(real)
    return real.astype(np.float64)


def rtn_autocorr_analytic(p: RTNParams, tau) -> float:
    """[C7/C8a] EXACT RTN dephasing autocorrelation  C(tau) = v^2 * exp(-2*gamma_sw*|tau|).

    This is the v^2-scaled latent autocorrelation (the frequency-noise autocorr  <delta_omega(0)
    delta_omega(tau)> with delta_omega = v*xi). The bare telegraph autocorr <xi(0)xi(tau)> =
    exp(-2*gamma_sw*|tau|) is this divided by v^2. Accepts scalar or array tau.
    """
    v = float(p.v)
    g = float(p.gamma_sw)
    tau_arr = np.asarray(tau, dtype=np.float64)
    out = (v * v) * np.exp(-2.0 * g * np.abs(tau_arr))
    if np.ndim(tau_arr) == 0:
        return float(out)
    return out.astype(np.float64)


def motional_narrowing_rate(p: RTNParams) -> float:
    """[C3] EXACT motional-narrowing (fast/weak v << gamma_sw) exponential-dephasing rate
    Gamma = v^2 / (2*gamma_sw).  L(t) -> exp(-Gamma*t) in this limit (the Markovian baseline)."""
    return float(p.v * p.v / (2.0 * p.gamma_sw))


def sum_lorentzian_spectrum_analytic(p: OneOverFParams, omega) -> float:
    """[C6] EXACT closed-form sum-of-Lorentzians spectrum (Dutta-Horn), the 1/f ANALYTIC target:

        S(omega) = sum_k v_k^2 * (4*gamma_k) / ((2*gamma_k)^2 + omega^2).

    Each RTN contributes a Lorentzian of HWHM 2*gamma_k (the autocorr decays at 2*gamma_k, so the
    one-sided PSD of v*xi(t) is the Fourier transform of v^2 exp(-2 gamma |tau|) = v^2 *
    4 gamma/((2 gamma)^2 + omega^2)). Log-spaced gamma_k + constant v_k -> S ~ 1/omega over the
    band. Accepts scalar or array omega. Deterministic (no sampling)."""
    omega_arr = np.asarray(omega, dtype=np.float64)
    acc = np.zeros_like(omega_arr, dtype=np.float64)
    for v, g in zip(p.v_list, p.gamma_list):
        acc = acc + (v * v) * (4.0 * g) / ((2.0 * g) ** 2 + omega_arr ** 2)
    if np.ndim(omega_arr) == 0:
        return float(acc)
    return acc.astype(np.float64)


# =========================================================================== #
# Telegraph samplers — explicit memory-ful SOURCE (seeded; pure numpy).        #
# =========================================================================== #
def sample_rtn_trajectory(p: RTNParams, t_grid, seed: int) -> np.ndarray:
    """Sample one RTN telegraph trajectory xi(t) in {+1,-1} on t_grid (seeded).

    Continuous-time telegraph process: in each sub-interval dt the +/-1 state flips with probability
    p_flip = (1 - exp(-2*gamma_sw*dt))/2 (the two-state Markov chain whose stationary autocorr is
    exp(-2*gamma_sw*dt)). The +/-1 stationary distribution is uniform, so the initial value is a fair
    coin. Returns a float64 array of +/-1, length len(t_grid).

    seed is an EXPLICIT int (vary per trajectory by passing seed+k); uses numpy.random.Generator —
    NEVER global/time RNG. Requires a uniform t_grid (constant dt).
    """
    tg = np.asarray(t_grid, dtype=np.float64)
    assert tg.ndim == 1 and tg.size >= 1, "sample_rtn_trajectory: t_grid must be 1-D non-empty."
    rng = np.random.default_rng(int(seed))
    xi = np.empty(tg.size, dtype=np.float64)
    xi[0] = 1.0 if rng.random() < 0.5 else -1.0
    if tg.size == 1:
        return xi
    dts = np.diff(tg)
    assert np.all(dts > 0.0), "sample_rtn_trajectory: t_grid must be strictly increasing."
    # constant-dt fast path (the canonical case); per-step flip prob otherwise.
    dt0 = float(dts[0])
    uniform_dt = bool(np.allclose(dts, dt0, rtol=1e-9, atol=1e-15))
    if uniform_dt:
        p_flip = 0.5 * (1.0 - np.exp(-2.0 * p.gamma_sw * dt0))
        flips = rng.random(tg.size - 1) < p_flip          # True where the state flips
        sign = np.where(flips, -1.0, 1.0)
        # cumulative product of +/-1 flip-signs propagates the telegraph state forward.
        xi[1:] = xi[0] * np.cumprod(sign)
    else:
        cur = xi[0]
        for i in range(1, tg.size):
            p_flip = 0.5 * (1.0 - np.exp(-2.0 * p.gamma_sw * float(dts[i - 1])))
            if rng.random() < p_flip:
                cur = -cur
            xi[i] = cur
    return xi


def sample_1f_trajectory(p: OneOverFParams, t_grid, seed: int) -> np.ndarray:
    """Sample one colored 1/f trajectory as the SUM of N independent RTN telegraphs, each weighted
    by its v_k: delta_omega(t) = sum_k v_k * xi_k(t).

    Returns the summed frequency-noise trajectory delta_omega(t) (rad/ns), float64, length len(t_grid).
    Each RTN gets a DISTINCT seed (seed + k) so the fluctuators are independent. (This returns the
    SOURCE field delta_omega; the per-RTN +/-1 telegraphs are internal.)
    """
    tg = np.asarray(t_grid, dtype=np.float64)
    acc = np.zeros(tg.size, dtype=np.float64)
    for k, rtn in enumerate(p.rtns()):
        xi_k = sample_rtn_trajectory(rtn, tg, seed=int(seed) + k)
        acc = acc + rtn.v * xi_k
    return acc


# =========================================================================== #
# The trajectory-averaged REDUCED qubit dephasing channel E(t) — the {E(t)}    #
# family the divisibility detector + wedge consume.                            #
# =========================================================================== #
def _phase_from_trajectory(v: float, xi_traj: np.ndarray, t_grid: np.ndarray) -> np.ndarray:
    """phi(t) = v * integral_0^t xi dt'  via cumulative trapezoid on t_grid (real float64 array)."""
    if t_grid.size == 1:
        return np.zeros(1, dtype=np.float64)
    dt = np.diff(t_grid)
    # trapezoidal increments of the +/-1 step function (xi is piecewise constant; trapezoid is exact
    # for the linear-interpolant convention and accurate for the step process at fine dt).
    incr = 0.5 * (xi_traj[1:] + xi_traj[:-1]) * dt
    integral = np.concatenate([[0.0], np.cumsum(incr)])
    return v * integral


def source_reduced_dephasing_channel(p, t: float, n_traj: int, seed: int,
                                     dim: int = 2, n_substep: int = 200):
    """The trajectory-AVERAGED REDUCED qubit dephasing channel E(t) at a single time t.

    Builds the MC estimate of the reduced coherence factor
        L_hat(t) = (1/n_traj) * sum_traj exp(i * phi_traj(t)),   phi_traj(t) = v * integral_0^t xi dt',
    by sampling n_traj telegraph trajectories on a fine sub-step grid [0, t] (n_substep points) and
    integrating the phase. The reduced dephasing channel acts on the qubit density matrix as
        rho_01 -> L_hat(t) * rho_01,   rho_10 -> conj(L_hat(t)) * rho_10,   populations preserved
    (a pure-dephasing channel — S2a: the source modulates frequency only, no |0>-|1> population
    transfer). Returns a (dim x dim) complex128 dephasing-factor matrix M such that the channel is
    E(rho)[i,j] = M[i,j] * rho[i,j] (an entrywise / Hadamard dephasing map). For dim=3 the |2> level
    is INERT (project convention): rows/cols touching |2> get factor 1 (no extra dephasing of/with
    the leakage level by THIS source).

    p may be an RTNParams (single fluctuator) OR a OneOverFParams (sum-of-RTNs); the phase is
    v * integral xi for RTN, or integral of delta_omega = sum_k v_k xi_k for 1/f.

    n_substep sets the phase-integration grid resolution (more -> tighter integral). seed is the
    explicit base seed; trajectory j uses seed + j (and 1/f's internal RTNs offset further). Returns
    (M, L_hat) so callers (the gtcheck) get the scalar coherence too.

    DECLARED (rule III): the MC estimate has standard error ~ 1/sqrt(n_traj) (bounded in the
    gtcheck's MC band). n_substep is a (c) integration-grid constant (its bias -> 0 as n_substep grows;
    the gtcheck reports the residual). dim in {2,3}; |2> inert is S2b scope.
    """
    assert dim in (2, 3), "source_reduced_dephasing_channel: dim must be 2 or 3."
    assert n_traj >= 1 and n_substep >= 2, "need n_traj>=1, n_substep>=2."
    t = float(t)
    t_grid = np.linspace(0.0, t, int(n_substep), dtype=np.float64)

    is_rtn = isinstance(p, RTNParams)
    is_1f = isinstance(p, OneOverFParams)
    assert is_rtn or is_1f, "p must be RTNParams or OneOverFParams."

    phases = np.empty(int(n_traj), dtype=np.float64)
    for j in range(int(n_traj)):
        if is_rtn:
            xi = sample_rtn_trajectory(p, t_grid, seed=int(seed) + j)
            phi = _phase_from_trajectory(p.v, xi, t_grid)
        else:
            # 1/f: phase is the integral of delta_omega(t) = sum_k v_k xi_k(t). Offset each
            # trajectory's seed block by n*j so the N internal RTNs never collide across trajectories.
            domega = sample_1f_trajectory(p, t_grid, seed=int(seed) + j * (p.n + 1))
            if t_grid.size == 1:
                phi = np.zeros(1, dtype=np.float64)
            else:
                dt = np.diff(t_grid)
                incr = 0.5 * (domega[1:] + domega[:-1]) * dt
                phi = np.concatenate([[0.0], np.cumsum(incr)])
        phases[j] = phi[-1]

    # MC coherence factor (complex128); for the symmetric model E[Im] -> 0 (finite-N residue).
    L_hat = np.mean(np.exp(1j * phases.astype(np.complex128)))
    L_hat = np.complex128(L_hat)

    # Build the entrywise dephasing-factor matrix M.
    M = np.ones((dim, dim), dtype=np.complex128)
    M[0, 1] = L_hat
    M[1, 0] = np.conj(L_hat)
    # diagonal = 1 (populations preserved); |2> (dim==3) inert -> already 1 everywhere it touches.
    return M, L_hat


def apply_dephasing_factor(M: np.ndarray, rho: np.ndarray) -> np.ndarray:
    """Apply the entrywise dephasing-factor map E(rho)[i,j] = M[i,j]*rho[i,j] (Hadamard product).
    Helper for callers/gtchecks that want the channel ACTION (not just the factor matrix)."""
    M = np.asarray(M, dtype=np.complex128)
    rho = np.asarray(rho, dtype=np.complex128)
    assert M.shape == rho.shape, "apply_dephasing_factor: shape mismatch."
    return M * rho


def dephasing_choi(M: np.ndarray) -> np.ndarray:
    """[C1 helper] Choi matrix of the entrywise-dephasing channel with factor matrix M.

    For a Hadamard/dephasing channel E(rho) = M (.) rho (entrywise), the Choi matrix (unnormalized,
    sum_ij |i><j| (x) E(|i><j|)) is  Choi[(i,k),(j,l)] = M[i,j] * delta_ik * delta_jl ... more
    directly: E(|i><j|) = M[i,j] |i><j|, so Choi = sum_ij |i><j| (x) M[i,j]|i><j|. We build it
    explicitly as a (dim^2 x dim^2) complex128 matrix. CP <=> Choi PSD; a pure-dephasing channel is
    CP iff M is a valid (PSD, unit-diagonal) correlation matrix. Returns the Choi matrix."""
    M = np.asarray(M, dtype=np.complex128)
    dim = M.shape[0]
    choi = np.zeros((dim * dim, dim * dim), dtype=np.complex128)
    for i in range(dim):
        for j in range(dim):
            # E(|i><j|) = M[i,j] |i><j|; Choi += |i><j| (x) E(|i><j|).
            block = np.zeros((dim, dim), dtype=np.complex128)
            block[i, j] = M[i, j]
            # |i><j| (x) block placed via Kronecker.
            outer_ij = np.zeros((dim, dim), dtype=np.complex128)
            outer_ij[i, j] = 1.0
            choi += np.kron(outer_ij, block)
    return choi


if __name__ == "__main__":
    # AUTHOR-only module: NO heavy run here. A trivial structural smoke that touches no MC sampling
    # beyond a tiny shape/branch check, so `python nm_source.py` is safe (the real validation is in
    # nm_source_gtcheck.py, run SERIALLY by the orchestrator).
    import sys

    _p_over = RTNParams(v=0.3, gamma_sw=1.0)    # v < gamma : overdamped branch
    _p_under = RTNParams(v=2.0, gamma_sw=1.0)   # v > gamma : revival branch
    print("nm_source structural smoke (NO heavy MC):", flush=True)
    print(f"  L_over(1.0)  = {rtn_coherence_analytic(_p_over, 1.0):.6f} (overdamped, real)", flush=True)
    print(f"  L_under(1.0) = {rtn_coherence_analytic(_p_under, 1.0):.6f} (revival branch, real)",
          flush=True)
    print(f"  C(0)=v^2={rtn_autocorr_analytic(_p_over, 0.0):.6f} ; "
          f"Gamma_mn={motional_narrowing_rate(_p_over):.6f}", flush=True)
    _onef = make_1f_params(v=0.1, gamma_min=1e-3, gamma_max=1e0, n=8)
    print(f"  1/f S(omega=0.1) = {sum_lorentzian_spectrum_analytic(_onef, 0.1):.6e} (N={_onef.n})",
          flush=True)
    sys.exit(0)

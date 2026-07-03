#!/usr/bin/env python
r"""CP-DIVISIBILITY (non-Markovianity) DETECTOR layer (Builder ② deliverable).

WHAT THIS IS
------------
A SOUND CP-divisibility detector for a single-qubit pure-DEPHASING family {E(t)}. Given the
reduced coherence L(t) (the qubit off-diagonal factor: rho_01 -> L(t) rho_01), the time-local
dephasing rate is

    gamma_phi(t) = - d/dt ln|L(t)|,

which goes NEGATIVE exactly when |L| REVIVES = the channel is NOT CP-divisible = non-Markovian
(information backflow). This module turns that into three independent detectors:

  - time_local_rate(L_func, t_grid)          : numerical gamma_phi(t) = -d/dt ln|L|;
  - rhp_measure(L_func, t_grid)              : RHP = integral of max(0, -gamma_phi) dt   [canonical];
  - blp_measure(channel_at_t, t_grid, pairs) : Breuer-Laine-Piilo trace-distance REVIVAL (independent
                                               second detector; optimal equatorial pair |+>,|->);
  - intermediate_map_cp(channel, t1, t2)     : min Choi eig of E(t2) o E(t1)^{-1} (divisibility
                                               definition DIRECTLY);
  - is_markovian(L_func, t_grid, tol)        : RHP ~ 0 AND BLP ~ 0.

THE PHYSICS (the (a)-exact basis this detector is sound against):
  * For pure dephasing E_t(rho)[i,j] = M_t[i,j] rho[i,j] with M_t[0,1]=L(t), the qubit Bloch
    coherence length is |L(t)|.  gamma_phi(t) = -d/dt ln|L(t)| (time-local generator rate).
  * CP-DIVISIBLE  <=>  gamma_phi(t) >= 0 for all t  <=>  |L| monotone non-increasing  <=>  the
    intermediate map E(t2) o E(t1)^{-1} (factor L(t2)/L(t1)) is CP for all t2>=t1, i.e.
    |L(t2)| <= |L(t1)|.  RHP = integral of the negative part of gamma_phi = total divisibility
    violation; = 0 iff CP-divisible.  (Rivas-Huelga-Plenio 2010.)
  * BLP information backflow: for the OPTIMAL antipodal equatorial pair |+>,|-> the trace distance
    D(E_t rho_+, E_t rho_-) = |L(t)|; non-monotonicity (any interval with dD/dt>0) = a revival =
    non-Markovian. BLP measure = sum over growth intervals of Delta D. (Breuer-Laine-Piilo 2009.)
  * For a KNOWN-MARKOVIAN exponential-dephasing channel L(t)=exp(-Gamma t) (a D[sqrt(Gamma) n]
    Lindblad), gamma_phi = +Gamma (constant >=0), |L| strictly decreasing => RHP=0 AND BLP=0. This
    is the C4 POSITIVE CONTROL theorem the detector MUST satisfy (reads 0 on a genuinely Markovian
    channel), independent of any source sim.

INDEPENDENT GROUND TRUTH (anti-circular, rule I):
  The detector is checked (in nm_divisibility_gtcheck.py) against (i) the L(t)=exp(-Gamma t)
  closed-form Markovian theorem (RHP=BLP=0) and (ii) Builder (1)'s ANALYTIC rtn_coherence_analytic
  (NOT the MC sim): gamma_phi from the closed-form L goes negative iff v>gamma_sw, the P1 boundary.
  The MC source sim's own output is NEVER the sole reference.

EPISTEMIC FRAME (METRICS.md):
  - gamma_phi = -d/dt ln|L|, RHP = int max(0,-gamma_phi), the |L| revival <=> non-CP-divisible
    equivalence, and the L=exp(-Gamma t) => RHP=0 theorem are (a) EXACT (premise / positive control).
  - the numerical-derivative scheme + the grid resolution + the tol thresholds are (c) design /
    gate; bounded in the gtcheck (the broken-control catches a biased derivative).

DISCIPLINE (HARD CONSTRAINTS):
  - AUTHOR-only: NO torch / GPU / QuTiP / heavy runs here. Pure numpy. The orchestrator runs the
    gtcheck SERIALLY.
  - complex128 wherever complex; the detector consumes |L| so it is robust to L's real/complex form.
  - every detector able to FAIL (a false-wedge detector reading >0 on Markovian is the toy this
    prevents); the gtcheck's broken-control MUST catch a biased derivative.

OWNERSHIP: Builder (2) owns ONLY nm_divisibility.py + nm_divisibility_gtcheck.py. Builder (1) owns
nm_source.py; Builder (3) owns nm_wedge.py. Do NOT touch theirs.
"""
from __future__ import annotations

from typing import Callable, List, Optional, Sequence, Tuple

import numpy as np

# numerical floor (project convention; src/qec_twin/numerics.py).
NUMERICAL_ZERO = 1e-12


# =========================================================================== #
# Coherence-magnitude helper (robust to L real or complex).                    #
# =========================================================================== #
def _coherence_magnitude(L_func: Callable[[np.ndarray], np.ndarray],
                         t_grid: np.ndarray) -> np.ndarray:
    """Evaluate |L(t)| on t_grid as a real float64 array, floored at NUMERICAL_ZERO.

    L_func(t) may return real (RTN analytic) or complex (general dephasing) values, scalar-or-array.
    We take |.| (the Bloch coherence length) since gamma_phi = -d/dt ln|L|. The floor avoids
    log(0) at exact coherence zeros (genuine |L|->0 crossings at the v>gamma revival nodes); the
    rate near such zeros is handled by the masking in time_local_rate.
    """
    L = np.asarray(L_func(np.asarray(t_grid, dtype=np.float64)))
    mag = np.abs(L).astype(np.float64)
    return mag


# =========================================================================== #
# (1) time-local dephasing rate  gamma_phi(t) = -d/dt ln|L(t)|.                 #
# =========================================================================== #
def time_local_rate(L_func: Callable[[np.ndarray], np.ndarray],
                    t_grid: Sequence[float],
                    return_mask: bool = False):
    """Numerical time-local dephasing rate gamma_phi(t) = -d/dt ln|L(t)| on t_grid.

    Method (careful at L->0 zeros / sign):
      * compute |L| on the grid, floor at NUMERICAL_ZERO;
      * y = ln|L|; gamma_phi = -dy/dt via numpy.gradient (2nd-order central in the interior,
        1st-order one-sided at the ends), which uses the (possibly non-uniform) t spacing exactly;
      * near a genuine coherence ZERO (|L| <= sqrt(NUMERICAL_ZERO)) ln|L| -> -inf and the finite
        difference is meaningless (a removable singularity of the rate at a revival node, not a
        physical divergence). Those samples are MASKED (set to NaN) so the RHP integral skips them
        rather than integrating a spurious +/- spike. The revival is still captured: |L| GROWS on
        the way OUT of the node, giving the negative-rate interval on the far side.

    gamma_phi >= 0  : CP-divisible locally (|L| decreasing);
    gamma_phi <  0  : non-CP-divisible (|L| reviving = information backflow).

    Returns gamma_phi (float64 array, same length as t_grid; NaN at masked zero-nodes).
    If return_mask: returns (gamma_phi, valid_mask) where valid_mask is False at masked samples.
    """
    t = np.asarray(t_grid, dtype=np.float64)
    assert t.ndim == 1 and t.size >= 3, "time_local_rate: need a 1-D t_grid with >=3 points."
    assert np.all(np.diff(t) > 0.0), "time_local_rate: t_grid must be strictly increasing."

    mag = _coherence_magnitude(L_func, t)
    # zero-node mask: |L| at/near a genuine revival node where ln|L| is singular.
    zero_eps = np.sqrt(NUMERICAL_ZERO)  # ~1e-6: well below any physical coherence of interest.
    valid = mag > zero_eps

    mag_floored = np.where(mag > NUMERICAL_ZERO, mag, NUMERICAL_ZERO)
    y = np.log(mag_floored)
    # numpy.gradient handles non-uniform spacing (2nd-order central interior, 1st-order ends).
    dydt = np.gradient(y, t, edge_order=2)
    gamma_phi = -dydt

    # mask the singular samples (and their immediate neighbours, whose central difference straddles
    # the node) so the RHP integrand skips them.
    masked = ~valid
    if np.any(masked):
        nbr = np.zeros_like(masked)
        idx = np.where(masked)[0]
        nbr[np.clip(idx - 1, 0, t.size - 1)] = True
        nbr[np.clip(idx + 1, 0, t.size - 1)] = True
        masked = masked | nbr
    gamma_phi = np.where(masked, np.nan, gamma_phi)
    valid_mask = ~masked

    if return_mask:
        return gamma_phi.astype(np.float64), valid_mask
    return gamma_phi.astype(np.float64)


# =========================================================================== #
# (2) RHP non-Markovianity = integral of the negative part of gamma_phi.       #
# =========================================================================== #
def rhp_measure(L_func: Callable[[np.ndarray], np.ndarray],
                t_grid: Sequence[float]) -> float:
    """RHP non-Markovianity measure = integral_0^T max(0, -gamma_phi(t)) dt  [the canonical detector].

    = 0  iff  gamma_phi(t) >= 0 everywhere  iff  the channel is CP-divisible (Markovian).
    > 0  iff  gamma_phi dips negative anywhere (|L| revives) = non-CP-divisible.

    Trapezoidal integration of the NEGATIVE-rate part over t_grid, skipping masked zero-node samples
    (NaN) so a revival node does not inject a spurious spike. The integrand is max(0,-gamma_phi),
    so a purely-positive (Markovian) rate integrates to EXACTLY 0 (positive control). Returns a
    non-negative float.
    """
    t = np.asarray(t_grid, dtype=np.float64)
    gamma_phi = time_local_rate(L_func, t)
    neg_part = np.maximum(0.0, -gamma_phi)          # non-negative integrand
    # treat masked (NaN) samples as 0 contribution (the node is measure-zero on the integral).
    neg_part = np.where(np.isnan(neg_part), 0.0, neg_part)
    # trapezoid rule, written manually so it is robust across numpy versions (numpy 2.0 removed
    # np.trapz; np.trapezoid is the 2.0 name) — sum of (y[k]+y[k+1])/2 * dt_k.
    rhp = float(np.sum(0.5 * (neg_part[:-1] + neg_part[1:]) * np.diff(t)))
    # clamp tiny negative round-off (the trapezoid of a >=0 integrand is >=0 up to fp noise).
    return rhp if rhp > 0.0 else 0.0


# =========================================================================== #
# Single-qubit dephasing-channel action (for the BLP + intermediate-map tests).#
# =========================================================================== #
def dephasing_channel_action(L_value: complex, rho: np.ndarray) -> np.ndarray:
    """Apply the single-qubit pure-dephasing channel with coherence factor L to rho (2x2):
        rho_00,rho_11 preserved;  rho_01 -> L rho_01;  rho_10 -> conj(L) rho_10.
    L_value is the scalar coherence L(t). Returns the evolved 2x2 complex128 density matrix."""
    rho = np.asarray(rho, dtype=np.complex128)
    assert rho.shape == (2, 2), "dephasing_channel_action: rho must be 2x2."
    L = np.complex128(L_value)
    out = rho.copy()
    out[0, 1] = L * rho[0, 1]
    out[1, 0] = np.conj(L) * rho[1, 0]
    return out


def _trace_distance(rho1: np.ndarray, rho2: np.ndarray) -> float:
    """Trace distance D(rho1,rho2) = (1/2) ||rho1-rho2||_1 = (1/2) sum |eigenvalues(rho1-rho2)|.
    rho1-rho2 is Hermitian, so the trace norm is the sum of |eigenvalues| (eigvalsh)."""
    delta = np.asarray(rho1, dtype=np.complex128) - np.asarray(rho2, dtype=np.complex128)
    # Hermitize against fp asymmetry, then eigvalsh.
    delta = 0.5 * (delta + delta.conj().T)
    ev = np.linalg.eigvalsh(delta)
    return 0.5 * float(np.sum(np.abs(ev)))


def equatorial_state_pairs() -> List[Tuple[np.ndarray, np.ndarray]]:
    """The canonical antipodal equatorial Bloch pair (|+>,|->) — for pure dephasing this is the
    BLP-OPTIMAL pair (it maximizes the trace-distance revival; the coherence is fully in rho_01).

    |+> = (1/2)[[1,1],[1,1]],  |-> = (1/2)[[1,-1],[-1,1]]. Returns a 1-element list of (rho_+, rho_-)
    so blp_measure can be handed a panel of pairs and maximize over them (the BLP definition is a
    sup over state pairs; for pure dephasing the equatorial pair attains it)."""
    plus = 0.5 * np.array([[1.0, 1.0], [1.0, 1.0]], dtype=np.complex128)
    minus = 0.5 * np.array([[1.0, -1.0], [-1.0, 1.0]], dtype=np.complex128)
    return [(plus, minus)]


def blp_measure(channel_at_t: Callable[[float], complex],
                t_grid: Sequence[float],
                state_pairs: Optional[Sequence[Tuple[np.ndarray, np.ndarray]]] = None) -> float:
    """Breuer-Laine-Piilo (BLP) trace-distance REVIVAL non-Markovianity measure.

    channel_at_t(t) returns the scalar coherence factor L(t) at time t (the dephasing channel is then
    rho_01 -> L(t) rho_01). For each candidate antipodal pair (rho1,rho2), evolve both under E_t,
    form D_pair(t) = trace_distance(E_t rho1, E_t rho2), and SUM the POSITIVE increments
    Delta D = D(t_{k+1}) - D(t_k) over intervals where D GROWS (dD/dt > 0 = information backflow).
    BLP measure = MAX over the candidate pairs of that summed revival (the sup in the BLP definition).

    For pure dephasing and the equatorial pair, D(t) = |L(t)|, so any |L| revival contributes; a
    monotone-decreasing |L| (Markovian) gives 0 growth => BLP = 0 (positive control). state_pairs
    defaults to the BLP-optimal equatorial pair. Returns a non-negative float.
    """
    t = np.asarray(t_grid, dtype=np.float64)
    assert t.ndim == 1 and t.size >= 2, "blp_measure: need a 1-D t_grid with >=2 points."
    assert np.all(np.diff(t) > 0.0), "blp_measure: t_grid must be strictly increasing."
    if state_pairs is None:
        state_pairs = equatorial_state_pairs()

    # precompute L(t) on the grid once.
    Lt = np.array([np.complex128(channel_at_t(float(tt))) for tt in t], dtype=np.complex128)

    best = 0.0
    for (rho1, rho2) in state_pairs:
        D = np.empty(t.size, dtype=np.float64)
        for k in range(t.size):
            e1 = dephasing_channel_action(Lt[k], rho1)
            e2 = dephasing_channel_action(Lt[k], rho2)
            D[k] = _trace_distance(e1, e2)
        dD = np.diff(D)
        revival = float(np.sum(np.maximum(0.0, dD)))  # sum of positive increments
        if revival > best:
            best = revival
    return best if best > 0.0 else 0.0


# =========================================================================== #
# (4) intermediate-map CP test  E(t2) o E(t1)^{-1}  (divisibility, directly).   #
# =========================================================================== #
def _dephasing_choi_from_factor(Lval: complex) -> np.ndarray:
    """Choi matrix (4x4, complex128) of the single-qubit dephasing channel rho_01 -> L rho_01.
    Build via the factor matrix M = [[1,L],[conj(L),1]] and Choi[(i,k),(j,l)] = M[i,j] delta_ik
    delta_jl  =>  E(|i><j|) = M[i,j]|i><j|, Choi = sum_ij |i><j| (x) M[i,j]|i><j|.
    CP <=> Choi PSD <=> |L| <= 1 (the dephasing factor matrix M is a valid correlation matrix)."""
    L = np.complex128(Lval)
    M = np.array([[1.0, L], [np.conj(L), 1.0]], dtype=np.complex128)
    dim = 2
    choi = np.zeros((dim * dim, dim * dim), dtype=np.complex128)
    for i in range(dim):
        for j in range(dim):
            outer_ij = np.zeros((dim, dim), dtype=np.complex128)
            outer_ij[i, j] = 1.0
            block = np.zeros((dim, dim), dtype=np.complex128)
            block[i, j] = M[i, j]
            choi += np.kron(outer_ij, block)
    return choi


def intermediate_map_cp(channel: Callable[[float], complex], t1: float, t2: float) -> float:
    """Intermediate-map CP test (the CP-divisibility DEFINITION directly): the min Choi eigenvalue
    of the propagator V(t2,t1) = E(t2) o E(t1)^{-1}.

    channel(t) returns the scalar coherence L(t). For pure dephasing E(t1) has factor L(t1) and its
    inverse has factor 1/L(t1) (defined where L(t1) != 0), so the intermediate dephasing map V has
    factor L(t2)/L(t1). V is CP iff its Choi is PSD iff |L(t2)/L(t1)| <= 1, i.e. min Choi eig >= 0.

    Returns the min eigenvalue of the 4x4 Choi of V (real; >= -NUMERICAL_ZERO => CP =>
    locally CP-divisible on [t1,t2]; < 0 => non-CP-divisible = a divisibility violation). Raises if
    L(t1) is ~0 (the intermediate map is undefined at a coherence zero; caller picks t1 off nodes).
    """
    L1 = np.complex128(channel(float(t1)))
    L2 = np.complex128(channel(float(t2)))
    assert abs(L1) > NUMERICAL_ZERO, \
        "intermediate_map_cp: L(t1) ~ 0; intermediate map E(t2) o E(t1)^{-1} undefined at a node."
    factor = L2 / L1
    choi = _dephasing_choi_from_factor(factor)
    # Choi is Hermitian; eigvalsh gives real eigenvalues.
    ev = np.linalg.eigvalsh(0.5 * (choi + choi.conj().T))
    return float(np.min(ev.real))


# =========================================================================== #
# (5) the verdict: Markovian  <=>  RHP ~ 0 AND BLP ~ 0.                          #
# =========================================================================== #
def is_markovian(L_func: Callable[[np.ndarray], np.ndarray],
                 t_grid: Sequence[float],
                 tol: float = 1e-6,
                 channel_at_t: Optional[Callable[[float], complex]] = None) -> bool:
    """Markovian (CP-divisible) verdict: RHP <= tol AND BLP <= tol.

    L_func(t) is the coherence callable for RHP. channel_at_t(t) (the scalar L(t)) is used for BLP;
    if None it defaults to L_func evaluated at the scalar t. tol is the (c) numerical gate (defaulting
    to 1e-6; the gtcheck sizes it to the numerical-derivative + MC band). Returns True iff BOTH
    independent detectors read ~0 (a single detector is not trusted alone)."""
    if channel_at_t is None:
        channel_at_t = lambda tt: np.complex128(np.asarray(L_func(np.asarray(float(tt)))).item())
    rhp = rhp_measure(L_func, t_grid)
    blp = blp_measure(channel_at_t, t_grid)
    return (rhp <= tol) and (blp <= tol)


if __name__ == "__main__":
    # AUTHOR-only module: NO heavy run here. A trivial structural smoke on closed-form coherences
    # (no MC, no source sim) so `python nm_divisibility.py` is safe. The real validation (C4 positive
    # control + broken control + the v=gamma_sw boundary) is in nm_divisibility_gtcheck.py, run
    # SERIALLY by the orchestrator.
    import sys

    # known-Markovian L(t)=exp(-Gamma t): RHP and BLP must read ~0.
    Gamma = 0.5
    t_grid = np.linspace(0.05, 8.0, 400)
    L_markov = lambda t: np.exp(-Gamma * np.asarray(t, dtype=np.float64))
    chan_markov = lambda tt: np.complex128(np.exp(-Gamma * float(tt)))
    rhp_m = rhp_measure(L_markov, t_grid)
    blp_m = blp_measure(chan_markov, t_grid)

    # a deliberately non-monotone |L| (toy revival) to show the detectors FIRE.
    L_revival = lambda t: np.exp(-0.3 * np.asarray(t, dtype=np.float64)) * np.cos(1.5 * np.asarray(t, dtype=np.float64))
    chan_revival = lambda tt: np.complex128(np.exp(-0.3 * float(tt)) * np.cos(1.5 * float(tt)))
    rhp_r = rhp_measure(L_revival, t_grid)
    blp_r = blp_measure(chan_revival, t_grid)

    print("nm_divisibility structural smoke (closed-form L only, NO MC):", flush=True)
    print(f"  Markovian L=exp(-Gt):  RHP={rhp_m:.3e}  BLP={blp_m:.3e}  (both must be ~0)", flush=True)
    print(f"  revival   L=e^-.3t cos: RHP={rhp_r:.3e}  BLP={blp_r:.3e}  (both must be >0)", flush=True)
    # intermediate-map CP on the Markovian channel: |L(t2)|<|L(t1)| => min Choi eig ~ 0 (CP).
    mineig_m = intermediate_map_cp(chan_markov, 1.0, 2.0)
    print(f"  Markovian intermediate-map min Choi eig (t1=1,t2=2) = {mineig_m:.3e} (>= ~0 => CP)",
          flush=True)
    is_m = is_markovian(L_markov, t_grid, tol=1e-3, channel_at_t=chan_markov)
    print(f"  is_markovian(Markovian) = {is_m}  (expected True)", flush=True)
    sys.exit(0)

r"""crow_joynt classical-field null (the independent-GT) + the phase covariance closed forms.

The sigma_z-only sector is a Gaussian collective pure dephasing (crow_joynt 1309.6383): the reduced
record equals a CLASSICAL Gaussian average of random sigma_z rotations exp(-i S_z phi_r) per round,
with round-window phase covariance Sigma_{rs} matched to the mode's symmetrized two-time correlation.
We push this classical field through the SAME dual-axis instrument (NO mode, 16-dim) and take the
Gaussian average by EXACT 3D Gauss-Hermite quadrature. This is the constructive (not K=0-by-fiat)
independent reproduction of the dephasing-sector record.

Extracted VERBATIM from outputs/twin_validation/notion3_relaxation_dualaxis_run.py, EXCEPT:
  - _gamma_of_t is copied from notion3_quantum_vs_classical_run.py as an OPTIONAL numerical cross-check
    of the gamma_unit_closed closed form (the primary source cross-checks them to 1e-9).
  - the ft/n3 indirection is removed (canonical package functions called directly).

Boundary: CPU exact-DM feasibility-only; evaluator-side. No physical ground truth (FORMAL).
"""

from __future__ import annotations

import math

import numpy as np
from numpy.polynomial.hermite_e import hermegauss
from scipy.integrate import cumulative_trapezoid

from .carrier import (
    _extract_x_full,
    _extract_z_full,
    _initial_rho_dual,
    dual_extract,
)
from .gksl import I2, SZ2
from .observables import (
    K_stat_binary,
    K_stat_joint,
    M_ALPHABET,
    M_mem_stat,
    exact_cmi_bits,
    project_axis,
)


# --------------------------------------------------------------------------- #
# crow_joynt CLASSICAL-FIELD NULL: Gamma_unit + Sigma covariance (closed form)  #
# + 3D Gauss-Hermite average of the classical sigma_z field through the SAME    #
# dual-axis instrument (NO mode, 16-dim).                                       #
# --------------------------------------------------------------------------- #
def gamma_unit_closed(tau, zeta, gamma):
    """Gamma_unit(tau) = int_0^tau (tau-t) e^{-gamma t} cos(zeta t) dt (g factored out). Scout-A closed form."""
    den = gamma * gamma + zeta * zeta
    I0 = (math.exp(-gamma * tau) * (-gamma * math.cos(zeta * tau) + zeta * math.sin(zeta * tau)) + gamma) / den
    a = complex(gamma, -zeta)
    I1 = ((1.0 - np.exp(-a * tau) * (1.0 + a * tau)) / (a * a)).real
    return float(tau * I0 - I1)


def sigma_offdiag_closed(m, tau, zeta, gamma):
    """Sigma_{r,s}, m=|r-s|>=1: Re[ e^{-p m tau} 2(cosh(p tau)-1)/p^2 ], p=gamma-i zeta. Scout-A closed form."""
    p = complex(gamma, -zeta)
    val = np.exp(-p * m * tau) * 2.0 * (np.cosh(p * tau) - 1.0) / (p * p)
    return float(val.real)


def build_sigma(R, tau, zeta, gamma):
    """R x R Toeplitz phase covariance. Diagonal = 2 Gamma_unit(tau); off-diagonal = sigma_offdiag_closed(|r-s|)."""
    diag = 2.0 * gamma_unit_closed(tau, zeta, gamma)
    S = np.empty((R, R), dtype=float)
    for r in range(R):
        for s in range(R):
            S[r, s] = diag if r == s else sigma_offdiag_closed(abs(r - s), tau, zeta, gamma)
    return S


def _gamma_of_t(t, zeta, gamma, g, nf=20001):
    """Gamma(t)=int_0^t (t-tau)Re C(tau)dtau, Re C(tau)=g^2 e^{-gamma tau} cos(zeta tau). Closed-form theorem.

    Copied VERBATIM from notion3_quantum_vs_classical_run.py as the OPTIONAL numerical cross-check of the
    gamma_unit_closed closed form (with g=1.0: _gamma_of_t(tau,zeta,gamma,1.0) == gamma_unit_closed(tau,zeta,gamma)
    to ~1e-9). Not on the hot path -- gamma_unit_closed is canonical.
    """
    A = g * g
    tau = np.linspace(0.0, float(t), nf)
    reC = A * np.exp(-gamma * tau) * np.cos(zeta * tau)
    P0 = cumulative_trapezoid(reC, tau, initial=0.0)
    P1 = cumulative_trapezoid(tau * reC, tau, initial=0.0)
    return float((tau * P0 - P1)[-1])


def field_null_dual_P_all(*, zeta, gamma, g0z, g1z, tau, n_gh):
    """crow_joynt classical-field null: Gaussian sigma_z field (cov Sigma) through the dual-axis instrument.

    NO mode (16-dim data+ancilla). Per round r: apply exp(-i S_z phi_r) to the data, then the SAME dual-axis
    extract/measure/reset. Gaussian-average over phi ~ N(0, Sigma) by EXACT 3D Gauss-Hermite quadrature.
    Returns (P_all, P_skip) -- the field-null joint record. NOTE: K on it is NOT 0 -- the dual (X,Z) measurement
    projects to the BELL basis (!= the sigma_z-dephasing Z-comp basis), so a classical sigma_z field yields a
    small GENUINE K (~3e-4); crow_joynt guarantees CHANNEL simulability, not record-K=0 under a non-commuting
    measurement. This null's role is G-repro (it reproduces the quantum sigma_z record), a classically-achievable
    dephasing floor.
    """
    R = 3
    Sigma = build_sigma(R, tau, zeta, gamma)
    Lchol = np.linalg.cholesky(Sigma)               # Sigma = L L^T
    x, w = hermegauss(n_gh)                          # int e^{-x^2/2} f dx = sum w f(x); E[f]=sum w f /sqrt(2pi)
    wn = w / math.sqrt(2.0 * math.pi)

    # S_z on the data (4) tensor I on (aX,aZ) -> 16-dim diagonal generator; mode absent (nmax=1).
    Sz_data = g0z * np.kron(SZ2, I2) + g1z * np.kron(I2, SZ2)        # 4x4
    Sz_full = np.kron(Sz_data, np.eye(4, dtype=complex))            # (d0,d1,aX,aZ) 16-dim, diagonal
    sz_diag = np.diag(Sz_full).real
    UX, UZ = _extract_x_full(1), _extract_z_full(1)                 # 16-dim (nmax=1)
    rho0 = _initial_rho_dual(1)

    P_all = {k: 0.0 for k in [(m1, m2, m3) for m1 in M_ALPHABET for m2 in M_ALPHABET for m3 in M_ALPHABET]}
    P_skip = {k: 0.0 for k in [(m1, m3) for m1 in M_ALPHABET for m3 in M_ALPHABET]}

    def rot(phi_r):
        d = np.exp(-1j * sz_diag * phi_r)
        return np.outer(d, d.conj())                # R rho R^dag = (d d*^T) elementwise; return the mask

    # 3D Gauss-Hermite over z; phi = Lchol @ z
    for i in range(n_gh):
        for j in range(n_gh):
            for k in range(n_gh):
                z = np.array([x[i], x[j], x[k]], dtype=float)
                phi = Lchol @ z
                weight = wn[i] * wn[j] * wn[k]
                masks = [rot(phi[r]) for r in range(R)]

                def idle_r(rho, r):
                    return masks[r] * rho           # elementwise phase rotation (diagonal unitary conjugation)

                r1 = idle_r(rho0, 0)
                br1 = dual_extract(r1, 1, UX, UZ)
                for m1 in M_ALPHABET:
                    a1 = br1[m1]
                    r2 = idle_r(a1, 1)
                    br2 = dual_extract(r2, 1, UX, UZ)
                    for m2 in M_ALPHABET:
                        a2 = br2[m2]
                        r3 = idle_r(a2, 2)
                        br3 = dual_extract(r3, 1, UX, UZ)
                        for m3 in M_ALPHABET:
                            P_all[(m1, m2, m3)] += weight * float(np.trace(br3[m3]).real)
                    # skip round-2 measurement: apply round-2 field rotation (no measure) then round-3
                    r_ev = idle_r(idle_r(a1, 1), 2)
                    br_sk = dual_extract(r_ev, 1, UX, UZ)
                    for m3 in M_ALPHABET:
                        P_skip[(m1, m3)] += weight * float(np.trace(br_sk[m3]).real)
    return P_all, P_skip


def field_null_point(*, zeta, gamma, g0z, g1z, tau, n_gh):
    Pa, Ps = field_null_dual_P_all(zeta=zeta, gamma=gamma, g0z=g0z, g1z=g1z, tau=tau, n_gh=n_gh)
    norm = sum(Pa.values())
    PaX, PsX = project_axis(Pa, 0), project_axis(Ps, 0)
    PaZ, PsZ = project_axis(Pa, 1), project_axis(Ps, 1)
    return {"K_joint": K_stat_joint(Pa, Ps), "K_X": K_stat_binary(PaX, PsX), "K_Z": K_stat_binary(PaZ, PsZ),
            "M_mem": M_mem_stat(Pa), "CMI": exact_cmi_bits(Pa), "P_all": Pa, "P_skip": Ps,
            "norm": float(norm)}

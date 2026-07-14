r"""Bosonic GKSL primitives for the shared-bath (pseudomode) carrier.

Canonical, package-native home for the boson algebra + the SHARED multi-component Liouvillian on
the REDUCED (d0,d1,mode) space (dim 4*nmax): sigma_z dephasing + sigma_minus EMISSION into one
shared mode, mode-loss collapse. Column-stacking (vec(B)=B.T.reshape(-1)) convention throughout.

Extracted VERBATIM from:
  - constants I2/SZ2/SM2/SX2/H1 <- outputs/twin_validation/notion3_relaxation_dualaxis_run.py
  - boson_ops <- outputs/twin_validation/quantum_backaction_fairtest.py
  - build_L2 (-> build_shared_bath_liouvillian) / round_superop2 (-> round_superop)
    <- notion3_relaxation_dualaxis_run.py

Boundary: exact-DM feasibility-only (reduced superop is (4*nmax)^2 sq); CPU; evaluator-side.
No physical ground truth (oracles are FORMAL).
"""

from __future__ import annotations

import math

import numpy as np
from scipy.linalg import expm

# --------------------------------------------------------------------------- #
# 1-qubit constants (from the primary source).                                 #
# --------------------------------------------------------------------------- #
I2 = np.eye(2, dtype=complex)
SZ2 = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
SM2 = np.array([[0.0, 1.0], [0.0, 0.0]], dtype=complex)  # sigma_minus = |0><1| (lowering |1>->|0>)
SX2 = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
H1 = (1.0 / math.sqrt(2.0)) * np.array([[1.0, 1.0], [1.0, -1.0]], dtype=complex)


def boson_ops(nmax):
    b = np.zeros((nmax, nmax), dtype=complex)
    for n in range(1, nmax):
        b[n - 1, n] = math.sqrt(n)
    return b, b.conj().T, b.conj().T @ b


# --------------------------------------------------------------------------- #
# SHARED multi-component Liouvillian on the REDUCED (d0,d1,mode) space (dim     #
# 4*nmax). Column-stacking (vec(B)=B.T.reshape(-1)), same convention as v2      #
# build_L2 / ft.build_L. The two ancillas are NOT in L (idle spectators).       #
# --------------------------------------------------------------------------- #
def build_shared_bath_liouvillian(nmax, zeta, gamma, g0z, g1z, g0m, g1m):
    """Shared sigma_z-dephasing + sigma_minus-EMISSION GKSL on (d0,d1,mode).

    H = zeta b^dag b + (g0z sz0 + g1z sz1)(b+b^dag) + [(g0m sminus0 + g1m sminus1) b^dag + h.c.]
    c = sqrt(2 gamma) b (mode loss). Reuses boson_ops for b/bdag/num (verbatim boson algebra).
    """
    b, bdag, num = boson_ops(nmax)
    Sz0 = np.kron(SZ2, I2)   # sz on d0 (data 4-block, MSB-first over d0,d1)
    Sz1 = np.kron(I2, SZ2)   # sz on d1
    Sm0 = np.kron(SM2, I2)   # sminus on d0
    Sm1 = np.kron(I2, SM2)   # sminus on d1
    Scoup_z = g0z * Sz0 + g1z * Sz1              # collective dephasing coupling (Hermitian, diagonal in Z)
    Scoup_m = g0m * Sm0 + g1m * Sm1              # collective emission coupling (non-Hermitian)
    H = zeta * np.kron(np.eye(4, dtype=complex), num)
    H = H + np.kron(Scoup_z, b + bdag)                           # sigma_z dephasing
    H = H + np.kron(Scoup_m, bdag) + np.kron(Scoup_m.conj().T, b)  # sigma_minus emission (JC/RWA), Hermitian
    c = math.sqrt(2.0 * gamma) * np.kron(np.eye(4, dtype=complex), b)
    dloc = 4 * nmax
    Id = np.eye(dloc, dtype=complex)
    L = -1j * (np.kron(Id, H) - np.kron(H.T, Id))
    cdc = c.conj().T @ c
    L = L + np.kron(c.conj(), c) - 0.5 * np.kron(Id, cdc) - 0.5 * np.kron(cdc.T, Id)
    return L, dloc


def round_superop(nmax, zeta, gamma, g0z, g1z, g0m, g1m, tau):
    L, dloc = build_shared_bath_liouvillian(nmax, zeta, gamma, g0z, g1z, g0m, g1m)
    return expm(L * tau), dloc

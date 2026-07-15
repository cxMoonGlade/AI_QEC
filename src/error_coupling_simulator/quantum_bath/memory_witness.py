r"""Bäcker et al. entanglement-based quantum-memory witness diagnostic.

Bäcker, Beyer, Strunz, Phys. Rev. Lett. 132, 060402 (2024) [arXiv:2310.01205], Theorem 1: for two-time dynamics with Choi
states chi_1 (over [0,t1]) and chi_2 (over [0,t2]),

    E#[chi(t1)] < E[chi(t2)]   =>   QUANTUM memory is REQUIRED (no classical-memory realization exists).

E = an entanglement monotone (here concurrence C), E# = entanglement of ASSISTANCE (C# = the max-average
entanglement extractable by measuring one side). For 2 qubits both have a closed form from the same
Wootters lambda_i: with lambda_i = sqrt(eig(rho rho~)) sorted DESC (rho~ = (sy(x)sy) rho* (sy(x)sy)),

    C(rho)  = max(0, lambda_1 - lambda_2 - lambda_3 - lambda_4)   [Wootters concurrence]
    C#(rho) = lambda_1 + lambda_2 + lambda_3 + lambda_4           [concurrence of assistance]

For the paper's zero-temperature amplitude-damping example the reduced-channel Choi state is rank two and
C# = C, so a concurrence revival can satisfy the inequality. This module evaluates the same quantities for the
declared Jaynes--Cummings vacuum-mode model. Interpreting a numerical violation as a quantum-memory conclusion
still requires checking every hypothesis of the cited theorem for that reduced-map family; the implementation is
a bounded formal diagnostic, not a production-record verdict.

Choi state of the reduced channel E(t) = Tr_mode[ U_t( . (x) |vac><vac| ) U_t^dag ]: prepare |phi+>_{S,A} (S =
system qubit coupled to the mode, A = spectator ancilla), tensor the mode in vacuum, evolve S+mode under the JC
GKSL for time t, trace out the mode -> chi(t) = (E(t) (x) I_A)|phi+><phi+| on (S,A).

Boundary: exact-density-matrix CPU execution (dimension = 4*nmax for system, ancilla, and mode),
evaluator-side, formal-oracle status. A bare monotone revival without the theorem's assisted-entanglement
bound is not accepted as a quantum-memory witness.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.linalg import expm

from .gksl import I2, SM2, SZ2  # noqa: F401  (SZ2 kept for parity with gksl; SM2 = sigma_minus)
from .gksl import boson_ops

_SY = np.array([[0.0, -1j], [1j, 0.0]], dtype=complex)
_SYY = np.kron(_SY, _SY)


def _jc_sae_liouvillian(g, gamma, zeta, nmax):
    """JC (S,A,mode) GKSL (column-stacking): H = zeta b^dag b + g(sm_S b^dag + sp_S b); collapse sqrt(2 gamma) b.
    S (system) couples to the mode; A (ancilla) is an identity spectator. dim = 4*nmax (S,A,mode)."""
    b, bdag, num = boson_ops(nmax)
    I4 = np.eye(4, dtype=complex)
    H = zeta * np.kron(I4, num) + g * (np.kron(np.kron(SM2, I2), bdag) + np.kron(np.kron(SM2.conj().T, I2), b))
    c = math.sqrt(2.0 * gamma) * np.kron(I4, b)
    D = 4 * nmax
    Id = np.eye(D, dtype=complex)
    L = -1j * (np.kron(Id, H) - np.kron(H.T, Id))
    cdc = c.conj().T @ c
    L = L + np.kron(c.conj(), c) - 0.5 * np.kron(Id, cdc) - 0.5 * np.kron(cdc.T, Id)
    return L, D


def jc_reduced_choi(g, gamma, zeta, t, nmax):
    """Choi state chi(t) (4x4 on S,A) of the reduced qubit channel of the JC sigma_minus emission after time t."""
    L, D = _jc_sae_liouvillian(g, gamma, zeta, nmax)
    # |phi+>_{S,A} = (|00>+|11>)/sqrt2 ; MSB-first (S,A). tensor |vac>_mode.
    phi = np.zeros(4, dtype=complex); phi[0] = 1.0 / math.sqrt(2.0); phi[3] = 1.0 / math.sqrt(2.0)
    vac = np.zeros(nmax, dtype=complex); vac[0] = 1.0
    psi = np.kron(phi, vac)
    rho0 = np.outer(psi, psi.conj())
    rt = (expm(L * t) @ rho0.T.reshape(-1)).reshape(D, D).T                # unvec(E@vec) column-stacking
    r = rt.reshape(4, nmax, 4, nmax)
    chi = np.einsum("aibi->ab", r)                                        # trace out the mode -> 4x4 (S,A)
    return chi


def _wootters_lambdas(rho4):
    rho_t = _SYY @ rho4.conj() @ _SYY
    ev = np.linalg.eigvals(rho4 @ rho_t).real
    lam = np.sqrt(np.clip(ev, 0.0, None))
    return np.sort(lam)[::-1]


def concurrence(rho4):
    lam = _wootters_lambdas(rho4)
    return float(max(0.0, lam[0] - lam[1] - lam[2] - lam[3]))


def concurrence_of_assistance(rho4):
    lam = _wootters_lambdas(rho4)
    return float(lam.sum())


def quantum_memory_witness(g, gamma, zeta, tau, nmax, n_t=40):
    """Evaluate the Bäcker inequality over a grid ``t in (0, 2*tau]``.

    ``inequality_violated`` records whether a sampled pair satisfies
    ``C#[chi(t1)] < C[chi(t2)]``. ``False`` is inconclusive: it does not establish
    classical memory or the absence of quantum memory. Scientific interpretation of a
    positive flag requires the theorem-hypothesis audit described in the module boundary.

    The result also reports the sampled concurrence curves, their extrema, the first
    violating pair, and the concurrence-revival magnitude.
    """
    ts = np.linspace(2.0 * tau / n_t, 2.0 * tau, n_t)
    # propagate the SAME Choi state on a fixed dt step (one expm), not a fresh expm(L*t) per point.
    L, D = _jc_sae_liouvillian(g, gamma, zeta, nmax)
    dt = ts[1] - ts[0]
    Estep = expm(L * ts[0]), expm(L * dt)            # (initial jump to ts[0], then the per-step propagator)
    phi = np.zeros(4, dtype=complex); phi[0] = 1.0 / math.sqrt(2.0); phi[3] = 1.0 / math.sqrt(2.0)
    vac = np.zeros(nmax, dtype=complex); vac[0] = 1.0
    v = np.kron(phi, vac); rho0 = np.outer(v, v.conj())
    vec = Estep[0] @ rho0.T.reshape(-1)
    C = np.empty(n_t); Csharp = np.empty(n_t)
    for k in range(n_t):
        if k > 0:
            vec = Estep[1] @ vec
        rt = vec.reshape(D, D).T
        chi = np.einsum("aibi->ab", rt.reshape(4, nmax, 4, nmax))
        lam = _wootters_lambdas(chi)
        C[k] = max(0.0, lam[0] - lam[1] - lam[2] - lam[3])
        Csharp[k] = lam.sum()
    fired = None
    for i in range(n_t):
        for j in range(i + 1, n_t):
            if Csharp[i] < C[j] - 1e-9:
                fired = (float(ts[i]), float(ts[j]), float(Csharp[i]), float(C[j]))
                break
        if fired:
            break
    # concurrence revival = non-monotonicity (max after the running minimum exceeds it)
    revival = 0.0
    running_min = C[0]
    for k in range(1, n_t):
        running_min = min(running_min, C[k])
        revival = max(revival, C[k] - running_min)
    return {"inequality_violated": fired is not None, "fired_t1_t2": fired,
            "concurrence_revival": float(revival), "C_max": float(C.max()), "C_min": float(C.min()),
            "Csharp_max": float(Csharp.max()), "ts": ts.tolist(), "C": C.tolist(), "Csharp": Csharp.tolist()}

from __future__ import annotations

r"""Backer et al. quantum-memory witness (Control 3) -- is the finite-gamma memory QUANTUM or CLASSICAL?

Backer, Beyer, Strunz, PRL 132, 230401 (2024) [arXiv:2310.01205], Theorem 1: for two-time dynamics with Choi
states chi_1 (over [0,t1]) and chi_2 (over [0,t2]),

    E#[chi(t1)] < E[chi(t2)]   =>   QUANTUM memory is REQUIRED (no classical-memory realization exists).

E = an entanglement monotone (here concurrence C), E# = entanglement of ASSISTANCE (C# = the max-average
entanglement extractable by measuring one side). For 2 qubits both have a closed form from the same
Wootters lambda_i: with lambda_i = sqrt(eig(rho rho~)) sorted DESC (rho~ = (sy(x)sy) rho* (sy(x)sy)),

    C(rho)  = max(0, lambda_1 - lambda_2 - lambda_3 - lambda_4)   [Wootters concurrence]
    C#(rho) = lambda_1 + lambda_2 + lambda_3 + lambda_4           [concurrence of assistance]

Backer's key result: for ZERO-TEMPERATURE amplitude damping the reduced-channel Choi is rank-2 with C# = C, and
C(t) is NON-monotonous in the non-Markovian regime (a concurrence revival) => there ALWAYS exist t2>t1 with
C(t1) < C(t2) => quantum memory REQUIRED. Our JC sigma_minus emission into a VACUUM mode IS zero-T amplitude
damping on the reduced qubit, so the criterion applies directly and is computed from single-time tomography of
the reduced dynamics -- NO process-tensor reconstruction.

Choi state of the reduced channel E(t) = Tr_mode[ U_t( . (x) |vac><vac| ) U_t^dag ]: prepare |phi+>_{S,A} (S =
system qubit coupled to the mode, A = spectator ancilla), tensor the mode in vacuum, evolve S+mode under the JC
GKSL for time t, trace out the mode -> chi(t) = (E(t) (x) I_A)|phi+><phi+| on (S,A).

Boundary: exact-DM CPU (dim = 4*nmax for S,A,mode); teacher/evaluator-side; SIMULATOR frame (FORMAL oracle).

RETIRED sibling (2026-07-07): the entropic / negativity-BACKFLOW witnesses
(entropic_memory_witness_single/_two_qubit) + their machinery (negativity, von_neumann_entropy,
_revival_fire, _two_qubit_*) were RETRACTED as quantum-memory witnesses (a bare monotone revival =
RHP non-Markovianity, forgeable by classical RTN dephasing; lit 2601.18822, 1608.05970) and REMOVED
from the reachable package -- record in retired/quantum_bath/memory_witness_entropic_backflow_2026-07-07.py.
The genuine quantum-memory statement is quantum_memory_witness (the Backer C#(t1)<C(t2) violation) below.
"""
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
    """Backer Theorem 1 over a time grid t in (0, 2*tau]: QUANTUM memory REQUIRED if exists t1<t2 with
    C#[chi(t1)] < C[chi(t2)]. Returns the verdict + the concurrence curves + the firing (t1,t2) if any.

    Also reports whether C(t) is non-monotonous (the zero-T AD signature, where C#=C so the criterion reduces to
    a concurrence revival) and the max Choi rank (rank-2 => C#=C exactly, Backer's zero-T case).
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
    return {"quantum_memory_required": fired is not None, "fired_t1_t2": fired,
            "concurrence_revival": float(revival), "C_max": float(C.max()), "C_min": float(C.min()),
            "Csharp_max": float(Csharp.max()), "ts": ts.tolist(), "C": C.tolist(), "Csharp": Csharp.tolist()}

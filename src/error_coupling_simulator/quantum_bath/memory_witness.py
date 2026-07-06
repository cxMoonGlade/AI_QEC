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
"""
import math

import numpy as np
from scipy.linalg import expm

from .carrier import apply_idle_reduced
from .gksl import I2, SM2, SZ2  # noqa: F401  (SZ2 kept for parity with gksl; SM2 = sigma_minus)
from .gksl import boson_ops, build_shared_bath_liouvillian

_SY = np.array([[0.0, -1j], [1j, 0.0]], dtype=complex)
_SYY = np.kron(_SY, _SY)


def _jc_sae_liouvillian(g, gamma, zeta, nmax):
    """JC (S,A,mode) GKSL (column-stacking): H = zeta b^dag b + g(sm_S b^dag + sp_S b); collapse sqrt(2 gamma) b.
    S (system) couples to the mode; A (ancilla) is an identity spectator. dim = 4*nmax (S,A,mode)."""
    b, bdag, num = boson_ops(nmax)
    smS = np.kron(np.kron(SM2, I2), np.eye(nmax, dtype=complex))          # sigma_minus on S, I on (A,mode)
    spS = smS.conj().T
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


# =========================================================================== #
# BACKFLOW / NON-MARKOVIANITY witness for the FULL 2-QUBIT SHARED BATH.          #
# *** RETRACTED as a quantum-memory witness (2026-07-06, Control 0b + lit). ***  #
# Signature = a NON-MONOTONIC (revived) entanglement monotone (NEGATIVITY) of    #
# the reduced-channel Choi = entanglement BACKFLOW = RHP non-CP-divisibility =   #
# NON-MARKOVIANITY. This is NOT Backer's criterion. Backer Thm 1 is E#[chi1] <   #
# E[chi2] -- the entanglement EXCEEDING the CLASSICAL-MEMORY BOUND E# (the '#',   #
# entanglement of ASSISTANCE). A bare revival DROPS the '#', so it cannot        #
# separate quantum memory from classical non-Markovian memory. PROVEN forgeable: #
# Control 0b -- classical RTN dephasing (manifestly classical, backflow) FIRES    #
# this witness (negativity revival 6.1e-2) while Backer C#(t1)<C(t2) stays        #
# SILENT on it. Lit: 2601.18822 (2026) "backflow witnesses MEMORY, not           #
# quantumness per se"; 1608.05970 (NM necessary-not-sufficient for revival);     #
# Backer's own applied witness 2510.19522 uses E#<E, not revival. USE ONLY as a  #
# non-Markovianity/backflow diagnostic. For a genuine quantum-memory statement:  #
# the C# form (single-qubit quantum_memory_witness) or a process-tensor witness  #
# (Giarmatzi 1811.03722). The entropic S(chi1)<S(chi2) form (2501.17660, project #
# note) is ALSO invalid (fires trivially). von_neumann_entropy = diagnostic only.#
# =========================================================================== #
def von_neumann_entropy(rho):
    """S(rho) = -tr[rho log2 rho], zero-eigenvalue regularized (reported diagnostic)."""
    ev = np.linalg.eigvalsh(0.5 * (rho + rho.conj().T)).real
    ev = ev[ev > 1e-12]
    return float(-np.sum(ev * np.log2(ev)))


def negativity(rho, dA):
    """Entanglement negativity N = (||rho^{T_A}||_1 - 1)/2 = sum of |negative eigenvalues of the ancilla partial
    transpose|. rho is (dA*dA)x(dA*dA) on (system dA) (x) (ancilla dA). A proper monotone for any dimension."""
    r = rho.reshape(dA, dA, dA, dA)                 # (sys_ket, anc_ket, sys_bra, anc_bra)
    rTA = r.transpose(0, 3, 2, 1).reshape(dA * dA, dA * dA)   # partial transpose on the ancilla
    ev = np.linalg.eigvalsh(0.5 * (rTA + rTA.conj().T)).real
    return float(-np.sum(ev[ev < 0.0]))


def _two_qubit_choi_rho0(nmax):
    """|phi+>_{(d0,d1),(aX,aZ)} (x) |vac>_mode as a 16*nmax density matrix. |phi+> = (1/2) sum_j |j>|j>, index
    (j<<2)|j for j in 0..3 -> {0,5,10,15} in the (d0,d1,aX,aZ) 16-block."""
    ket = np.zeros(16, dtype=complex)
    for j in range(4):
        ket[(j << 2) | j] = 0.5
    vac = np.zeros(nmax, dtype=complex); vac[0] = 1.0
    full = np.kron(ket, vac)
    return np.outer(full, full.conj())


def _two_qubit_shared_choi(gm, gamma, zeta, t, nmax, r=1.0):
    """Choi chi(t) (16x16 on system=(d0,d1) (x) ancilla=(aX,aZ)) of the 2-qubit reduced channel of the SHARED-bath
    sigma_minus emission (relaxation-only). Reuses the carrier apply_idle_reduced with the Choi ancilla (aX,aZ)
    as the 4-dim spectator, then traces out the mode. Single-t convenience (the witness propagates instead)."""
    L, _dloc = build_shared_bath_liouvillian(nmax, zeta, gamma, 0.0, 0.0, gm, gm * r)
    rt = apply_idle_reduced(expm(L * t), _two_qubit_choi_rho0(nmax), nmax)
    return np.einsum("aibi->ab", rt.reshape(16, nmax, 16, nmax))


def _revival_fire(vals):
    """Backflow REVIVAL detector: fires if exists t1<t2 with vals[t1] < vals[t2] (the monotone RISES after
    falling => entanglement backflow). revival = max rise above the running minimum. Correct for an ENTANGLEMENT
    monotone (negativity/concurrence): a revival = a rise. (NOT for entropy, whose backflow is a DROP.)
    *** This is an RHP NON-MARKOVIANITY / backflow detector, NOT a quantum-memory witness: a classical
    non-Markovian process (RTN dephasing) produces the SAME revival (proven: Control 0b; lit: 2601.18822 (2026)
    "backflow witnesses MEMORY, not quantumness per se"; 1608.05970 NM necessary-not-sufficient). Do NOT read a
    firing here as 'quantum memory' -- use the C# classical-bound form (quantum_memory_witness) for that. ***"""
    n = len(vals)
    fired = None
    revival = 0.0
    running_min = vals[0]
    for j in range(1, n):
        for i in range(j):
            if vals[i] < vals[j] - 1e-9:
                fired = (i, j, float(vals[i]), float(vals[j]))
                break
        running_min = min(running_min, vals[j])
        revival = max(revival, vals[j] - running_min)
        if fired:
            break
    return fired, float(revival)


def entropic_memory_witness_single(g, gamma, zeta, tau, nmax, n_t=40):
    """BACKFLOW / NON-MARKOVIANITY witness on the SINGLE-qubit reduced channel. Propagates the Choi state
    (2 expm). Fires => entanglement backflow => NON-MARKOVIANITY (NOT quantum memory -- RETRACTED 2026-07-06,
    Control 0b; a bare revival drops Backer's classical bound '#'). For the genuine single-qubit quantum-memory
    statement use quantum_memory_witness (C#(t1)<C(t2), the E#<E classical-bound violation). Reports the entropy
    curve as a diagnostic. (Name kept for API stability; the criterion is a negativity revival = backflow.)"""
    ts = np.linspace(2.0 * tau / n_t, 2.0 * tau, n_t)
    L, D = _jc_sae_liouvillian(g, gamma, zeta, nmax)
    E0, Estep = expm(L * ts[0]), expm(L * (ts[1] - ts[0]))
    phi = np.zeros(4, dtype=complex); phi[0] = 1.0 / math.sqrt(2.0); phi[3] = 1.0 / math.sqrt(2.0)
    vac = np.zeros(nmax, dtype=complex); vac[0] = 1.0
    v = np.kron(phi, vac)
    vec = E0 @ np.outer(v, v.conj()).T.reshape(-1)
    N, S = [], []
    for k in range(n_t):
        if k > 0:
            vec = Estep @ vec
        chi = np.einsum("aibi->ab", vec.reshape(D, D).T.reshape(4, nmax, 4, nmax))
        N.append(negativity(chi, 2))
        S.append(von_neumann_entropy(chi))
    fired, revival = _revival_fire(N)
    return {"quantum_memory_required": fired is not None, "fired_ij": fired, "negativity_revival": revival,
            "negativity": N, "entropy": S, "ts": ts.tolist()}


def entropic_memory_witness_two_qubit(gm, gamma, zeta, tau, nmax, r=1.0, n_t=40):
    """BACKFLOW / NON-MARKOVIANITY witness on the FULL 2-qubit SHARED-BATH reduced channel (d=4 system,
    Choi 16x16). Fires (negativity RISES after falling = entanglement backflow) => the 2-qubit reduced channel
    is NON-MARKOVIAN (RHP non-CP-divisibility). *** RETRACTED as a quantum-memory witness (2026-07-06, Control
    0b): a bare negativity revival is NOT Backer's criterion -- it drops the classical-memory bound '#'
    (E#[chi1]<E[chi2]) and so cannot separate quantum memory from classical non-Markovian memory. PROVEN
    forgeable: classical RTN dephasing fires it (2601.18822 (2026): "backflow witnesses MEMORY, not quantumness
    per se"). For a genuine d>2 quantum-memory claim use negativity-of-assistance (E# form) or a process-tensor
    witness (Giarmatzi 1811.03722). *** Propagates the 16*nmax Choi state via apply_idle_reduced (2 expm)."""
    ts = np.linspace(2.0 * tau / n_t, 2.0 * tau, n_t)
    L, _dloc = build_shared_bath_liouvillian(nmax, zeta, gamma, 0.0, 0.0, gm, gm * r)
    E0, Estep = expm(L * ts[0]), expm(L * (ts[1] - ts[0]))
    rho = apply_idle_reduced(E0, _two_qubit_choi_rho0(nmax), nmax)
    N, S = [], []
    for k in range(n_t):
        if k > 0:
            rho = apply_idle_reduced(Estep, rho, nmax)
        chi = np.einsum("aibi->ab", rho.reshape(16, nmax, 16, nmax))
        N.append(negativity(chi, 4))
        S.append(von_neumann_entropy(chi))
    fired, revival = _revival_fire(N)
    return {"quantum_memory_required": fired is not None, "fired_ij": fired, "negativity_revival": revival,
            "negativity": N, "entropy": S, "ts": ts.tolist()}

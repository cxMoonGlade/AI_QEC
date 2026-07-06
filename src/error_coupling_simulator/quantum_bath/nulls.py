from __future__ import annotations

r"""Incoherent amplitude-damping (AD) null family + the model-free record-distance discriminator.

The MATCHED classical-relaxation nulls for the sigma_minus (relaxation) sector: incoherent AD (no
coherence GENERATION), Markovian and non-Markovian (a 2-state classical latent), toward ANY Bloch
axis (the dual-axis instrument is basis-symmetric => K/K_X/K_Z are all forgeable). The honest
discriminator is min record-distance (TV) from the quantum shared-mode record to this whole family.

Extracted VERBATIM from outputs/twin_validation/notion3_relaxation_dualaxis_run.py; the only change is
removing the ft/n3 indirection (canonical package functions called directly). tv_distance lives in
observables (imported here).

Boundary: CPU exact-DM (16-dim, nmax=1); teacher/evaluator-side. No physical ground truth (FORMAL).
"""

import math

import numpy as np
from scipy.linalg import expm

from .carrier import (
    _extract_x_full,
    _extract_z_full,
    _initial_rho_dual,
    _on_qubit4,
    dual_extract,
)
from .gksl import SM2
from .observables import (
    K_stat_binary,
    K_stat_joint,
    M_ALPHABET,
    M_mem_stat,
    exact_cmi_bits,
    project_axis,
    tv_distance,
)


# --------------------------------------------------------------------------- #
# CLASSICAL-RELAXATION NULL: incoherent amplitude damping (CP-divisible, no     #
# mode, no coherence-generation) through the SAME dual-axis instrument -- the   #
# MATCHED genuinely-Markovian null for the RELAXATION sector.                   #
# --------------------------------------------------------------------------- #
def _ad_channel_data(rho, p):
    """Incoherent amplitude damping (prob p per round) on BOTH data qubits (independent), 16-dim (nmax=1).

    AD Kraus E0=diag(1,sqrt(1-p)), E1=[[0,sqrt(p)],[0,0]] (|1>-> |0> w.p. p, coherence x sqrt(1-p)). Non-unital,
    Markovian, NO coherence GENERATION (a classical population jump + coherence decay) -- the honest incoherent
    version of the quantum emission. Ancillas + (trivial) mode untouched.
    """
    s, rr = math.sqrt(1.0 - p), math.sqrt(p)
    E0 = np.array([[1.0, 0.0], [0.0, s]], dtype=complex)
    E1 = np.array([[0.0, rr], [0.0, 0.0]], dtype=complex)
    out = np.zeros_like(rho)
    for E in (E0, E1):                         # AD on d0
        Eq = _on_qubit4(E, 0)
        out = out + Eq @ rho @ Eq.conj().T
    out2 = np.zeros_like(rho)
    for E in (E0, E1):                         # AD on d1
        Eq = _on_qubit4(E, 1)
        out2 = out2 + Eq @ out @ Eq.conj().T
    return out2


# --------------------------------------------------------------------------- #
# GENERAL incoherent AD relaxing toward an ARBITRARY Bloch axis n(theta,phi).   #
# --------------------------------------------------------------------------- #
def _axis_ad_kraus(p, theta, phi):
    """AD Kraus relaxing toward the Bloch axis n(theta,phi): E_k = U E_k^Z U^dag, U = Rz(phi) Ry(theta)
    (takes +Z -> n). E0=diag(1,sqrt(1-p)), E1=[[0,sqrt(p)],[0,0]] in the Z frame. INCOHERENT (no coherence
    generation in its OWN relaxation basis), non-unital, CPTP -- a legitimate incoherent process for ANY axis."""
    ct, st = math.cos(theta / 2.0), math.sin(theta / 2.0)
    Ry = np.array([[ct, -st], [st, ct]], dtype=complex)
    Rz = np.array([[np.exp(-0.5j * phi), 0.0], [0.0, np.exp(0.5j * phi)]], dtype=complex)
    U = Rz @ Ry
    s, rr = math.sqrt(1.0 - p), math.sqrt(p)
    E0 = U @ np.array([[1.0, 0.0], [0.0, s]], dtype=complex) @ U.conj().T
    E1 = U @ np.array([[0.0, rr], [0.0, 0.0]], dtype=complex) @ U.conj().T
    return [E0, E1]


def _ad_channel_axis(rho, kraus0, kraus1):
    """Apply the per-qubit axis-AD Kraus (kraus for d0, d1 may differ -> biaxial/per-qubit-asymmetric) on 16-dim."""
    out = np.zeros_like(rho)
    for E in kraus0:                            # AD on d0
        Eq = _on_qubit4(E, 0)
        out = out + Eq @ rho @ Eq.conj().T
    out2 = np.zeros_like(rho)
    for E in kraus1:                            # AD on d1
        Eq = _on_qubit4(E, 1)
        out2 = out2 + Eq @ out @ Eq.conj().T
    return out2


def axis_ad_null_point(*, p0, theta0, phi0, p1=None, theta1=None, phi1=None, flip=None, p_lo=None, p_hi=None):
    """General incoherent-AD null: per-qubit AD toward (theta_i, phi_i) at prob p_i, dual-axis instrument.

    Markovian if flip is None; else NON-Markovian (a 2-state classical latent scales the AD prob by p_lo/p_hi,
    averaged over the 8 latent trajectories -> K AND classical memory, still INCOHERENT). d1 defaults to d0's
    axis/prob (collective) if p1/theta1/phi1 are None. Returns P_all + K_joint/K_X/K_Z + CMI + M_mem.
    """
    p1 = p0 if p1 is None else p1
    theta1 = theta0 if theta1 is None else theta1
    phi1 = phi0 if phi1 is None else phi1
    UX, UZ = _extract_x_full(1), _extract_z_full(1)
    rho0 = _initial_rho_dual(1)

    def chan(rho, scale):
        k0 = _axis_ad_kraus(min(1.0, p0 * scale), theta0, phi0)
        k1 = _axis_ad_kraus(min(1.0, p1 * scale), theta1, phi1)
        return _ad_channel_axis(rho, k0, k1)

    P_all = {(m1, m2, m3): 0.0 for m1 in M_ALPHABET for m2 in M_ALPHABET for m3 in M_ALPHABET}
    P_skip = {(m1, m3): 0.0 for m1 in M_ALPHABET for m3 in M_ALPHABET}
    if flip is None:
        latent_trajs = [((0, 0, 0), 1.0)]           # Markovian: single 'trajectory', scale=1
        scale_of = {0: 1.0}
    else:
        T = np.array([[1.0 - flip, flip], [flip, 1.0 - flip]], dtype=float)
        pi = np.array([0.5, 0.5], dtype=float)
        scale_of = {0: float(p_lo), 1: float(p_hi)}   # here p_lo/p_hi are SCALES on the base prob
        latent_trajs = [((x1, x2, x3), pi[x1] * T[x1, x2] * T[x2, x3])
                        for x1 in (0, 1) for x2 in (0, 1) for x3 in (0, 1)]
    for (xs, w) in latent_trajs:
        r1 = chan(rho0, scale_of[xs[0]])
        br1 = dual_extract(r1, 1, UX, UZ)
        for m1 in M_ALPHABET:
            a1 = br1[m1]
            r2 = chan(a1, scale_of[xs[1]])
            br2 = dual_extract(r2, 1, UX, UZ)
            for m2 in M_ALPHABET:
                a2 = br2[m2]
                r3 = chan(a2, scale_of[xs[2]])
                br3 = dual_extract(r3, 1, UX, UZ)
                for m3 in M_ALPHABET:
                    P_all[(m1, m2, m3)] += w * float(np.trace(br3[m3]).real)
            r_ev = chan(chan(a1, scale_of[xs[1]]), scale_of[xs[2]])
            br_sk = dual_extract(r_ev, 1, UX, UZ)
            for m3 in M_ALPHABET:
                P_skip[(m1, m3)] += w * float(np.trace(br_sk[m3]).real)
    norm = sum(P_all.values())
    PaX, PsX = project_axis(P_all, 0), project_axis(P_skip, 0)
    PaZ, PsZ = project_axis(P_all, 1), project_axis(P_skip, 1)
    return {"K_joint": K_stat_joint(P_all, P_skip), "K_X": K_stat_binary(PaX, PsX), "K_Z": K_stat_binary(PaZ, PsZ),
            "M_mem": M_mem_stat(P_all), "CMI": exact_cmi_bits(P_all), "P_all": P_all, "norm": float(norm)}


# --------------------------------------------------------------------------- #
# BROADER null class (#1): COHERENT single-qubit unitary + optional shared ZZ   #
# entangler + axis-AD (+ optional classical latent). Coherence is the           #
# attributed irreducible core of the shared-mode signature (#2); this null      #
# tests whether a COHERENT classical process reproduces the quantum record.     #
# --------------------------------------------------------------------------- #
def _su2(a, b, c):
    """General single-qubit unitary Rz(a) Ry(b) Rz(c) (the ZYZ Euler decomposition of SU(2))."""
    cb, sb = math.cos(b / 2.0), math.sin(b / 2.0)
    Ry = np.array([[cb, -sb], [sb, cb]], dtype=complex)
    Rz_a = np.array([[np.exp(-0.5j * a), 0.0], [0.0, np.exp(0.5j * a)]], dtype=complex)
    Rz_c = np.array([[np.exp(-0.5j * c), 0.0], [0.0, np.exp(0.5j * c)]], dtype=complex)
    return Rz_a @ Ry @ Rz_c


def _zz_unitary(phi):
    """exp(-i phi/2 Z0 Z1) on the data pair -- a CORRELATED (entangling) coherent step, 16-dim (I on ancillas).
    Z0Z1 eigenvalue = +1 on |00>,|11> and -1 on |01>,|10>; diagonal in the (d0,d1,aX,aZ) computational basis."""
    diag = np.ones(16, dtype=complex)
    for s in range(16):
        d0, d1 = (s >> 3) & 1, (s >> 2) & 1
        ev = 1.0 if d0 == d1 else -1.0
        diag[s] = np.exp(-0.5j * phi * ev)
    return np.diag(diag)


def coherent_ad_null_point(*, u0, u1, ad0, ad1, zz=0.0, flip=None, p_lo=None, p_hi=None):
    """BROADER null (#1): per-qubit COHERENT unitary u_i=(a,b,c) + optional shared ZZ(zz) entangler, THEN
    per-qubit axis-AD ad_i=(p,theta,phi), each round, through the dual-axis instrument. Markovian unless flip
    (a 2-state classical latent scaling the AD prob by p_lo/p_hi). HAS coherence (the unitaries) + optional
    correlation (zz) + optional classical memory (latent) -- tests whether a coherent classical process (NO
    quantum bath) reproduces the quantum shared-mode record. Returns P_all + K/CMI/M_mem stats."""
    Ucoh = _zz_unitary(zz) @ (_on_qubit4(_su2(*u0), 0) @ _on_qubit4(_su2(*u1), 1))
    p_a0, th_a0, ph_a0 = ad0
    p_a1, th_a1, ph_a1 = ad1
    UX, UZ = _extract_x_full(1), _extract_z_full(1)
    rho0 = _initial_rho_dual(1)

    def chan(rho, scale):
        rc = Ucoh @ rho @ Ucoh.conj().T                                # coherent unitary step
        k0 = _axis_ad_kraus(min(1.0, p_a0 * scale), th_a0, ph_a0)
        k1 = _axis_ad_kraus(min(1.0, p_a1 * scale), th_a1, ph_a1)
        return _ad_channel_axis(rc, k0, k1)                            # then incoherent axis-AD

    P_all = {(m1, m2, m3): 0.0 for m1 in M_ALPHABET for m2 in M_ALPHABET for m3 in M_ALPHABET}
    P_skip = {(m1, m3): 0.0 for m1 in M_ALPHABET for m3 in M_ALPHABET}
    if flip is None:
        latent_trajs = [((0, 0, 0), 1.0)]
        scale_of = {0: 1.0}
    else:
        T = np.array([[1.0 - flip, flip], [flip, 1.0 - flip]], dtype=float)
        pi = np.array([0.5, 0.5], dtype=float)
        scale_of = {0: float(p_lo), 1: float(p_hi)}
        latent_trajs = [((x1, x2, x3), pi[x1] * T[x1, x2] * T[x2, x3])
                        for x1 in (0, 1) for x2 in (0, 1) for x3 in (0, 1)]
    for (xs, w) in latent_trajs:
        r1 = chan(rho0, scale_of[xs[0]])
        br1 = dual_extract(r1, 1, UX, UZ)
        for m1 in M_ALPHABET:
            a1 = br1[m1]
            r2 = chan(a1, scale_of[xs[1]])
            br2 = dual_extract(r2, 1, UX, UZ)
            for m2 in M_ALPHABET:
                a2 = br2[m2]
                r3 = chan(a2, scale_of[xs[2]])
                br3 = dual_extract(r3, 1, UX, UZ)
                for m3 in M_ALPHABET:
                    P_all[(m1, m2, m3)] += w * float(np.trace(br3[m3]).real)
            r_ev = chan(chan(a1, scale_of[xs[1]]), scale_of[xs[2]])
            br_sk = dual_extract(r_ev, 1, UX, UZ)
            for m3 in M_ALPHABET:
                P_skip[(m1, m3)] += w * float(np.trace(br_sk[m3]).real)
    norm = sum(P_all.values())
    PaX, PsX = project_axis(P_all, 0), project_axis(P_skip, 0)
    PaZ, PsZ = project_axis(P_all, 1), project_axis(P_skip, 1)
    return {"K_joint": K_stat_joint(P_all, P_skip), "K_X": K_stat_binary(PaX, PsX), "K_Z": K_stat_binary(PaZ, PsZ),
            "M_mem": M_mem_stat(P_all), "CMI": exact_cmi_bits(P_all), "P_all": P_all, "norm": float(norm)}


_MTV_THETAS = tuple(i * math.pi / 6 for i in range(7))          # 0 .. pi
_MTV_PHIS = (0.0, math.pi / 2, math.pi)
_MTV_PS = (0.05, 0.1, 0.2, 0.3, 0.45, 0.6, 0.8)


def min_tv_to_incoherent(qP, *, nm_list=()):
    """COARSE per-point min record-distance (TV) from qP to the incoherent-AD family (collective Bloch-axis grid
    + a few non-Markovian latents). This is an UPPER BOUND on the true min (grid, no scipy) -- a fast in-run
    sanity that TV is large across the band; the DEFINITIVE adversarial min-TV (scipy + differential_evolution)
    is `notion3_incoherent_null_search.py`. Returns (min_tv, best_desc)."""
    best = (1e9, "")
    for th in _MTV_THETAS:
        for ph in _MTV_PHIS:
            for p in _MTV_PS:
                r = axis_ad_null_point(p0=p, theta0=th, phi0=ph)
                tv = tv_distance(qP, r["P_all"])
                if tv < best[0]:
                    best = (tv, f"collective th={th:.2f} ph={ph:.2f} p={p:.2f}")
    for (flip, plo, phi_) in nm_list:
        for th in (0.0, math.pi / 2):
            r = axis_ad_null_point(p0=0.5, theta0=th, phi0=0.0, flip=flip, p_lo=plo, p_hi=phi_)
            tv = tv_distance(qP, r["P_all"])
            if tv < best[0]:
                best = (tv, f"nonmarkov th={th:.2f} flip={flip} plo={plo} phi={phi_}")
    return best


def classical_ad_null_point(*, p):
    """Exact 3-round dual-axis (P_all,P_skip) for incoherent AD (prob p) -- the classical-relaxation matched null.

    Per round: apply incoherent AD to both data qubits, THEN the SAME dual-axis extract/measure/reset. NO mode
    (16-dim), Markovian (same channel each round). K here = the classically-achievable relaxation-sector K.
    """
    UX, UZ = _extract_x_full(1), _extract_z_full(1)
    rho0 = _initial_rho_dual(1)

    def idle(rho):
        return _ad_channel_data(rho, p)

    P_all, P_skip = {}, {}
    r1 = idle(rho0)
    br1 = dual_extract(r1, 1, UX, UZ)
    for m1 in M_ALPHABET:
        a1 = br1[m1]
        r2 = idle(a1)
        br2 = dual_extract(r2, 1, UX, UZ)
        for m2 in M_ALPHABET:
            a2 = br2[m2]
            r3 = idle(a2)
            br3 = dual_extract(r3, 1, UX, UZ)
            for m3 in M_ALPHABET:
                P_all[(m1, m2, m3)] = float(np.trace(br3[m3]).real)
        r_ev = idle(idle(a1))
        br_sk = dual_extract(r_ev, 1, UX, UZ)
        for m3 in M_ALPHABET:
            P_skip[(m1, m3)] = float(np.trace(br_sk[m3]).real)
    norm = sum(P_all.values())
    PaX, PsX = project_axis(P_all, 0), project_axis(P_skip, 0)
    PaZ, PsZ = project_axis(P_all, 1), project_axis(P_skip, 1)
    return {"K_joint": K_stat_joint(P_all, P_skip), "K_X": K_stat_binary(PaX, PsX), "K_Z": K_stat_binary(PaZ, PsZ),
            "M_mem": M_mem_stat(P_all), "CMI": exact_cmi_bits(P_all), "p": p, "P_all": P_all,
            "norm": float(norm)}


def classical_nonmarkov_ad_null_point(*, flip, p_lo, p_hi):
    """The STRICTEST classical-relaxation null (user 2026-07-05): incoherent AD MODULATED by a 2-state classical
    latent -- a memory-bearing classical relaxation. Exact over the 8 latent trajectories (relaxation analog of
    the notion3_quantum_vs_classical classical arm).

    Latent xi_r in {0,1}, transition flip, stationary pi=[.5,.5], AD prob p(xi)=p_lo/p_hi. For a FIXED latent
    trajectory the per-round map is an incoherent AD channel (no coherence GENERATION); the CLASSICAL latent
    (flip != 0.5) carries the MEMORY => this null has K AND CMI/M_mem (like the quantum). BUT it is INCOHERENT
    => its K_X (coherent complementary-axis imprint) ~ 0 regardless of parameters -- the genuine quantum
    signature the quantum sigma_minus emission must EXCEED. No mode (16-dim).
    """
    T = np.array([[1.0 - flip, flip], [flip, 1.0 - flip]], dtype=float)
    pi = np.array([0.5, 0.5], dtype=float)
    p_of = {0: float(p_lo), 1: float(p_hi)}
    UX, UZ = _extract_x_full(1), _extract_z_full(1)
    rho0 = _initial_rho_dual(1)
    P_all = {(m1, m2, m3): 0.0 for m1 in M_ALPHABET for m2 in M_ALPHABET for m3 in M_ALPHABET}
    P_skip = {(m1, m3): 0.0 for m1 in M_ALPHABET for m3 in M_ALPHABET}
    for x1 in (0, 1):
        for x2 in (0, 1):
            for x3 in (0, 1):
                w = pi[x1] * T[x1, x2] * T[x2, x3]
                r1 = _ad_channel_data(rho0, p_of[x1])
                br1 = dual_extract(r1, 1, UX, UZ)
                for m1 in M_ALPHABET:
                    a1 = br1[m1]
                    r2 = _ad_channel_data(a1, p_of[x2])
                    br2 = dual_extract(r2, 1, UX, UZ)
                    for m2 in M_ALPHABET:
                        a2 = br2[m2]
                        r3 = _ad_channel_data(a2, p_of[x3])
                        br3 = dual_extract(r3, 1, UX, UZ)
                        for m3 in M_ALPHABET:
                            P_all[(m1, m2, m3)] += w * float(np.trace(br3[m3]).real)
                    r_ev = _ad_channel_data(_ad_channel_data(a1, p_of[x2]), p_of[x3])
                    br_sk = dual_extract(r_ev, 1, UX, UZ)
                    for m3 in M_ALPHABET:
                        P_skip[(m1, m3)] += w * float(np.trace(br_sk[m3]).real)
    norm = sum(P_all.values())
    PaX, PsX = project_axis(P_all, 0), project_axis(P_skip, 0)
    PaZ, PsZ = project_axis(P_all, 1), project_axis(P_skip, 1)
    return {"K_joint": K_stat_joint(P_all, P_skip), "K_X": K_stat_binary(PaX, PsX), "K_Z": K_stat_binary(PaZ, PsZ),
            "M_mem": M_mem_stat(P_all), "CMI": exact_cmi_bits(P_all), "flip": flip, "p_lo": p_lo,
            "p_hi": p_hi, "P_all": P_all, "norm": float(norm)}


# --------------------------------------------------------------------------- #
# COLLECTIVE-AD null (Control 2): the Dicke collective jump L = sqrt(Gamma)     #
# (sigma-_d0 + sigma-_d1) -- correlated relaxation into a COMMON reservoir,     #
# INCOHERENT, memoryless. Fanchini 1301.3146: collective NM is super-additive  #
# => PER-QUBIT independent AD cannot reproduce it; Wang 1409.0172: the cross-   #
# term ∝ sqrt(J1 J2). Tests whether the r=1 Markovian residual (memory~0) is    #
# the collective structure.                                                     #
# --------------------------------------------------------------------------- #
def _collective_ad_superop(gamma_c, tau):
    """Column-stacking superop for one round of the collective AD channel D[c], c=sqrt(gamma_c)(sm_d0+sm_d1)
    on the 16-dim (d0,d1,aX,aZ) space (jump on the data pair, identity on the ancillas). No coherent H."""
    c = math.sqrt(gamma_c) * (_on_qubit4(SM2, 0) + _on_qubit4(SM2, 1))
    Id = np.eye(16, dtype=complex)
    cdc = c.conj().T @ c
    L = np.kron(c.conj(), c) - 0.5 * np.kron(Id, cdc) - 0.5 * np.kron(cdc.T, Id)
    return expm(L * tau)


def collective_ad_null_point(*, gamma_c, tau):
    """Control-2 null: the incoherent COLLECTIVE amplitude-damping channel (Dicke jump on the data pair),
    memoryless, through the dual-axis instrument. Returns P_all + K/CMI/M_mem. dim = 16 (no mode)."""
    E = _collective_ad_superop(gamma_c, tau)
    UX, UZ = _extract_x_full(1), _extract_z_full(1)
    rho0 = _initial_rho_dual(1)

    def chan(rho):
        return (E @ rho.T.reshape(-1)).reshape(16, 16).T          # column-stacking apply

    P_all, P_skip = {}, {}
    r1 = chan(rho0)
    br1 = dual_extract(r1, 1, UX, UZ)
    for m1 in M_ALPHABET:
        a1 = br1[m1]
        r2 = chan(a1)
        br2 = dual_extract(r2, 1, UX, UZ)
        for m2 in M_ALPHABET:
            a2 = br2[m2]
            r3 = chan(a2)
            br3 = dual_extract(r3, 1, UX, UZ)
            for m3 in M_ALPHABET:
                P_all[(m1, m2, m3)] = float(np.trace(br3[m3]).real)
        r_ev = chan(chan(a1))
        br_sk = dual_extract(r_ev, 1, UX, UZ)
        for m3 in M_ALPHABET:
            P_skip[(m1, m3)] = float(np.trace(br_sk[m3]).real)
    norm = sum(P_all.values())
    PaX, PsX = project_axis(P_all, 0), project_axis(P_skip, 0)
    PaZ, PsZ = project_axis(P_all, 1), project_axis(P_skip, 1)
    return {"K_joint": K_stat_joint(P_all, P_skip), "K_X": K_stat_binary(PaX, PsX), "K_Z": K_stat_binary(PaZ, PsZ),
            "M_mem": M_mem_stat(P_all), "CMI": exact_cmi_bits(P_all), "gamma_c": gamma_c, "P_all": P_all,
            "norm": float(norm)}

from __future__ import annotations

r"""Dual-ancilla dual-axis exact-DM carrier for the shared-bath (pseudomode) simulator.

2 data (d0,d1) + 2 ancilla (a_X,a_Z) + ONE shared bosonic mode, on the full (d0,d1,aX,aZ,mode) DM.
Per round: idle-evolve tau under the shared GKSL (reduced (d0,d1,mode) superop, both ancillas idle
spectators), then extract X_{d0}X_{d1} via a_X (H-conjugation) AND Z_{d0}Z_{d1} via a_Z (CX-parity),
SEQUENTIALLY. X0X1 and Z0Z1 commute => the joint per-round outcome m=(sX,sZ) is a valid instrument.
All branches kept => EXACT 3-round distribution (no Monte-Carlo).

Boundary: exact-DM feasibility-only (dim = 16*nmax); CPU; evaluator-side research carrier.
No physical ground truth (oracles are formal). Current carrier checks are registered in
``tests/test_quantum_bath_carrier_units.py`` and ``tests/test_quantum_bath.py``.
"""

import math

import numpy as np

from .gksl import H1, I2, SM2, SX2, SZ2, round_superop
from .observables import (
    K_stat_binary,
    K_stat_joint,
    M_ALPHABET,
    M_mem_stat,
    exact_cmi_bits,
    project_axis,
)

# --------------------------------------------------------------------------- #
# 4-qubit (d0,d1,a_X,a_Z) gates. MSB-first index: d0=bit3, d1=bit2, a_X=bit1,  #
# a_Z=bit0 (a_Z = LOW bit). Mode is a separate tensor factor (I_nmax).          #
# --------------------------------------------------------------------------- #
AX_BIT = np.array([(q >> 1) & 1 for q in range(16)])  # a_X population selector on the (d0,d1,aX,aZ) 16-block
AZ_BIT = np.array([q & 1 for q in range(16)])         # a_Z population selector


def _on_qubit4(op: np.ndarray, qidx: int) -> np.ndarray:
    """1-qubit `op` on qubit qidx (0=d0 MSB, 1=d1, 2=a_X, 3=a_Z LOW) tensor I on the other three -> 16x16."""
    mats = [I2, I2, I2, I2]
    mats[qidx] = op
    out = mats[0]
    for m in mats[1:]:
        out = np.kron(out, m)
    return out


def cnot4(control: int, target: int) -> np.ndarray:
    """4-qubit CNOT (qubit 0 = MSB = d0 ... qubit 3 = LSB = a_Z), manual permutation."""
    U = np.zeros((16, 16), dtype=complex)
    for s in range(16):
        bits = [(s >> 3) & 1, (s >> 2) & 1, (s >> 1) & 1, s & 1]
        if bits[control] == 1:
            bits[target] ^= 1
        U[(bits[0] << 3) | (bits[1] << 2) | (bits[2] << 1) | bits[3], s] = 1.0
    return U


def z_parity_unitary_4q() -> np.ndarray:
    """Z_{d0}Z_{d1} parity onto a_Z (a_X untouched): CX(d1->a_Z) CX(d0->a_Z)."""
    return cnot4(1, 3) @ cnot4(0, 3)


def x_parity_unitary_4q() -> np.ndarray:
    """X_{d0}X_{d1} parity onto a_X (a_Z untouched) via H-conjugation: Hd CX(d0->aX) CX(d1->aX) Hd."""
    Hd = _on_qubit4(H1, 0) @ _on_qubit4(H1, 1)
    return Hd @ (cnot4(1, 2) @ cnot4(0, 2)) @ Hd


# --------------------------------------------------------------------------- #
# EXACT reduced-idle GKSL apply on (d0,d1,mode) with BOTH ancillas as identity  #
# spectators (E_full = E_red tensor I_aX tensor I_aZ). Verified vs the full     #
# 16*nmax Liouvillian in factorization_check. Full DM order: (d0,d1,aX,aZ,mode).#
# --------------------------------------------------------------------------- #
def apply_idle_reduced(E_red: np.ndarray, rho: np.ndarray, nmax: int) -> np.ndarray:
    dr = 4 * nmax
    D = 16 * nmax
    # (d0,d1,aX,aZ,m) ket x (d0,d1,aX,aZ,m) bra
    r10 = rho.reshape(2, 2, 2, 2, nmax, 2, 2, 2, 2, nmax)
    # group R=(d0,d1,m), spectator S=(aX,aZ):  (d0k,d1k,mk, aXk,aZk, d0b,d1b,mb, aXb,aZb)
    r10b = r10.transpose(0, 1, 4, 2, 3, 5, 6, 9, 7, 8)
    r = r10b.reshape(dr, 4, dr, 4)               # (R_ket, S_ket, R_bra, S_bra), R=(d0,d1,m), S=(aX,aZ)
    rp = r.transpose(1, 3, 2, 0)                 # (S_ket, S_bra, R_bra, R_ket)
    v = rp.reshape(4, 4, dr * dr)                # col-vec over (R_bra, R_ket) per 4x4 spectator block
    outv = np.einsum("ij,skj->ski", E_red, v)    # apply reduced superop to each spectator block (I on aX,aZ)
    oo = outv.reshape(4, 4, dr, dr)              # (S_ket, S_bra, R_bra, R_ket)
    oo = oo.transpose(3, 0, 2, 1).reshape(dr, 4, dr, 4)   # (R_ket, S_ket, R_bra, S_bra)
    oo10 = oo.reshape(2, 2, nmax, 2, 2, 2, 2, nmax, 2, 2)  # (d0k,d1k,mk,aXk,aZk, d0b,d1b,mb,aXb,aZb)
    oo10 = oo10.transpose(0, 1, 3, 4, 2, 5, 6, 8, 9, 7)    # (d0,d1,aX,aZ,m) x (d0,d1,aX,aZ,m)
    return oo10.reshape(D, D)


# --------------------------------------------------------------------------- #
# ancilla-mediated extraction as EXACT quantum instruments on the full          #
# (d0,d1,aX,aZ,mode) DM: extract unitary, project one ancilla, reset it.         #
# --------------------------------------------------------------------------- #
def _extract_x_full(nmax: int) -> np.ndarray:
    return np.kron(x_parity_unitary_4q(), np.eye(nmax, dtype=complex))


def _extract_z_full(nmax: int) -> np.ndarray:
    return np.kron(z_parity_unitary_4q(), np.eye(nmax, dtype=complex))


def _branch_ax(rho: np.ndarray, nmax: int, mX: int) -> tuple[np.ndarray, float]:
    """Project a_X=|mX>, return (post-reset unnormalized branch, prob). a_Z + data + mode untouched; a_X->|0>."""
    D = 16 * nmax
    r = rho.reshape(2, 2, 2, 2, nmax, 2, 2, 2, 2, nmax)   # axis2=aXk, axis7=aXb
    sub = np.zeros_like(r)
    sub[:, :, mX, :, :, :, :, mX, :, :] = r[:, :, mX, :, :, :, :, mX, :, :]   # P rho P (a_X diagonal projector)
    p = float(np.einsum("abcde abcde ->", sub).real)
    traced = sub[:, :, mX, :, :, :, :, mX, :, :]          # (d0k,d1k,aZk,mk, d0b,d1b,aZb,mb)
    new = np.zeros_like(r)
    new[:, :, 0, :, :, :, :, 0, :, :] = traced            # reset a_X -> |0>
    return new.reshape(D, D), p


def _branch_az(rho: np.ndarray, nmax: int, mZ: int) -> tuple[np.ndarray, float]:
    """Project a_Z=|mZ>, return (post-reset unnormalized branch, prob). a_X + data + mode untouched; a_Z->|0>."""
    D = 16 * nmax
    r = rho.reshape(2, 2, 2, 2, nmax, 2, 2, 2, 2, nmax)   # axis3=aZk, axis8=aZb
    sub = np.zeros_like(r)
    sub[:, :, :, mZ, :, :, :, :, mZ, :] = r[:, :, :, mZ, :, :, :, :, mZ, :]
    p = float(np.einsum("abcde abcde ->", sub).real)
    traced = sub[:, :, :, mZ, :, :, :, :, mZ, :]          # (d0k,d1k,aXk,mk, d0b,d1b,aXb,mb)
    new = np.zeros_like(r)
    new[:, :, :, 0, :, :, :, :, 0, :] = traced            # reset a_Z -> |0>
    return new.reshape(D, D), p


def dual_extract(rho: np.ndarray, nmax: int, UX: np.ndarray, UZ: np.ndarray) -> dict:
    """Sequential dual-axis instrument: extract X (measure+reset a_X), then Z (measure+reset a_Z).

    Returns {(sX,sZ): post-instrument UNNORMALIZED branch} (trace = joint prob), all four branches kept.
    """
    rx = UX @ rho @ UX.conj().T
    out = {}
    for sX in (0, 1):
        bX, _ = _branch_ax(rx, nmax, sX)
        rz = UZ @ bX @ UZ.conj().T
        for sZ in (0, 1):
            bZ, _ = _branch_az(rz, nmax, sZ)
            out[(sX, sZ)] = bZ
    return out


def _initial_rho_dual(nmax: int) -> np.ndarray:
    """|+ +>_data |0>_aX |0>_aZ |vac>_mode."""
    plus = np.array([1.0, 1.0], dtype=complex) / math.sqrt(2.0)
    zero = np.array([1.0, 0.0], dtype=complex)
    data_anc = np.kron(np.kron(np.kron(plus, plus), zero), zero)   # (d0,d1,aX,aZ) 16-vector
    vac = np.zeros(nmax, dtype=complex); vac[0] = 1.0
    full = np.kron(data_anc, vac)
    return np.outer(full, full.conj())


# --------------------------------------------------------------------------- #
# QUANTUM arm: exact 3-round dual-axis (P_all, P_skip) for the shared bath.     #
# --------------------------------------------------------------------------- #
def quantum_dual_P_all(nmax, zeta, gamma, g0z, g1z, g0m, g1m, tau):
    E_red, _ = round_superop(nmax, zeta, gamma, g0z, g1z, g0m, g1m, tau)
    UX, UZ = _extract_x_full(nmax), _extract_z_full(nmax)
    rho0 = _initial_rho_dual(nmax)

    def idle(rho):
        return apply_idle_reduced(E_red, rho, nmax)

    P_all, P_skip = {}, {}
    r1 = idle(rho0)
    br1 = dual_extract(r1, nmax, UX, UZ)
    for m1 in M_ALPHABET:
        a1 = br1[m1]
        r2 = idle(a1)
        br2 = dual_extract(r2, nmax, UX, UZ)
        for m2 in M_ALPHABET:
            a2 = br2[m2]
            r3 = idle(a2)
            br3 = dual_extract(r3, nmax, UX, UZ)
            for m3 in M_ALPHABET:
                P_all[(m1, m2, m3)] = float(np.trace(br3[m3]).real)
        # skip round-2 MEASUREMENT: round-2 idle only (mode evolves), no extraction/measure; then round-3.
        r_ev = idle(idle(a1))
        br_sk = dual_extract(r_ev, nmax, UX, UZ)
        for m3 in M_ALPHABET:
            P_skip[(m1, m3)] = float(np.trace(br_sk[m3]).real)
    return P_all, P_skip


def dual_point(nmax, zeta, gamma, g0z, g1z, g0m, g1m, tau):
    Pa, Ps = quantum_dual_P_all(nmax, zeta, gamma, g0z, g1z, g0m, g1m, tau)
    norm = sum(Pa.values())
    assert abs(norm - 1.0) < 1e-8, f"quantum dual P_all not normalized: {norm}"
    PaX, PsX = project_axis(Pa, 0), project_axis(Ps, 0)
    PaZ, PsZ = project_axis(Pa, 1), project_axis(Ps, 1)
    return {"K_joint": K_stat_joint(Pa, Ps), "K_X": K_stat_binary(PaX, PsX), "K_Z": K_stat_binary(PaZ, PsZ),
            "M_mem": M_mem_stat(Pa), "CMI": exact_cmi_bits(Pa), "P_all": Pa, "P_skip": Ps,
            "norm": float(norm)}


# --------------------------------------------------------------------------- #
# QRT (reduced-map) null -- Luppi 2605.06427 Eq. 24: the SAME model but with the #
# mode RESET to vacuum each round, so each round is the reduced map Lambda_S     #
# (within-round coherence retained, cross-round mode MEMORY destroyed). Then     #
# eps_QRT = TV(exact [mode persists], QRT [mode reset]) IS the multitime memory  #
# term Phi_memory = Lambda^{A1(Q)} (Luppi Eq. 25) -- parameter-free, no fit.     #
# --------------------------------------------------------------------------- #
def _reset_mode_to_vacuum(rho: np.ndarray, nmax: int) -> np.ndarray:
    """Trace out the mode and re-tensor |vac><vac|_mode (Lambda_S starts each round from a fresh vacuum bath)."""
    r = rho.reshape(16, nmax, 16, nmax)              # (block,mode) x (block,mode), block=(d0,d1,aX,aZ)
    reduced16 = np.einsum("imjm->ij", r)             # partial trace over the mode -> 16x16 data+ancilla
    vac = np.zeros((nmax, nmax), dtype=complex); vac[0, 0] = 1.0
    return np.kron(reduced16, vac)


def quantum_dual_P_all_qrt(nmax, zeta, gamma, g0z, g1z, g0m, g1m, tau):
    """QRT-null (Luppi Eq. 24): identical to quantum_dual_P_all but the mode is reset to vacuum after each
    round's measurement, so each round applies the reduced map Lambda_S (no cross-round mode memory)."""
    E_red, _ = round_superop(nmax, zeta, gamma, g0z, g1z, g0m, g1m, tau)
    UX, UZ = _extract_x_full(nmax), _extract_z_full(nmax)
    rho0 = _initial_rho_dual(nmax)

    def idle(rho):
        return apply_idle_reduced(E_red, rho, nmax)

    def reset(rho):
        return _reset_mode_to_vacuum(rho, nmax)

    P_all, P_skip = {}, {}
    r1 = idle(rho0)
    br1 = dual_extract(r1, nmax, UX, UZ)
    for m1 in M_ALPHABET:
        a1 = reset(br1[m1])                          # QRT: fresh vacuum mode before the next round
        r2 = idle(a1)
        br2 = dual_extract(r2, nmax, UX, UZ)
        for m2 in M_ALPHABET:
            a2 = reset(br2[m2])
            r3 = idle(a2)
            br3 = dual_extract(r3, nmax, UX, UZ)
            for m3 in M_ALPHABET:
                P_all[(m1, m2, m3)] = float(np.trace(br3[m3]).real)
        # skip round-2 measurement: round-2 idle (fresh vacuum), reset, round-3 idle (fresh vacuum); NO measure
        r_ev = idle(reset(idle(a1)))
        br_sk = dual_extract(r_ev, nmax, UX, UZ)
        for m3 in M_ALPHABET:
            P_skip[(m1, m3)] = float(np.trace(br_sk[m3]).real)
    return P_all, P_skip


def dual_point_qrt(nmax, zeta, gamma, g0z, g1z, g0m, g1m, tau):
    """QRT-null record point (Luppi reduced-map null; mode reset each round)."""
    Pa, Ps = quantum_dual_P_all_qrt(nmax, zeta, gamma, g0z, g1z, g0m, g1m, tau)
    norm = sum(Pa.values())
    assert abs(norm - 1.0) < 1e-8, f"QRT dual P_all not normalized: {norm}"
    PaX, PsX = project_axis(Pa, 0), project_axis(Ps, 0)
    PaZ, PsZ = project_axis(Pa, 1), project_axis(Ps, 1)
    return {"K_joint": K_stat_joint(Pa, Ps), "K_X": K_stat_binary(PaX, PsX), "K_Z": K_stat_binary(PaZ, PsZ),
            "M_mem": M_mem_stat(Pa), "CMI": exact_cmi_bits(Pa), "P_all": Pa, "P_skip": Ps, "norm": float(norm)}

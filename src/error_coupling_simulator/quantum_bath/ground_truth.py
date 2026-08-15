from __future__ import annotations

r"""Anti-toy GROUND-TRUTH checks (Rule I: independent, non-circular reference computations).

Each check scores the shared-bath carrier against a reference DERIVED WITHOUT reference to the
carrier construction:
  * factorization_check      -- reduced idle (E_red tensor I_aX tensor I_aZ) == full 16*nmax Liouvillian.
  * extraction_gt_check      -- both ancillas read their parity deterministically on parity eigenstates.
  * two_qubit_indep_boson_gt -- sigma_z sector reduced coherences vs the independent-boson closed form.
  * sigma_minus_emission_gt  -- reduced p_e(t) (GKSL) vs the exact single-excitation amplitude ODE.
  * no_bath_sanity           -- bath off => flat Markov-0 record on both axes, K=0.

These are FORMAL oracles (implementation-bug catchers); there is no physical ground truth.
Current corruption and independence checks are in
``tests/test_quantum_bath_groundtruth_nulls_units.py`` and ``tests/test_quantum_bath.py``.
"""

import math

import numpy as np
from scipy.linalg import expm

from .carrier import (
    AX_BIT,
    AZ_BIT,
    _on_qubit4,
    apply_idle_reduced,
    dual_point,
    x_parity_unitary_4q,
    z_parity_unitary_4q,
)
from .crow_joynt import gamma_unit_closed
from .gksl import I2, SM2, SZ2, boson_ops, round_superop
from .observables import M_ALPHABET


def full_superop_bytes(nmax: int) -> float:
    D2 = (16 * nmax) ** 2
    return float(D2 * D2 * 16)


# --------------------------------------------------------------------------- #
# CONTROLS                                                                     #
# --------------------------------------------------------------------------- #
def factorization_check(nmax, zeta, gamma, g0z, g1z, g0m, g1m, tau) -> dict:
    """(fac) reduced-idle apply (E_red tensor I_aX tensor I_aZ) == full 16*nmax Liouvillian. Small nmax."""
    b, bdag, num = boson_ops(nmax)
    I16 = np.eye(16, dtype=complex)
    Sz0 = _on_qubit4(SZ2, 0); Sz1 = _on_qubit4(SZ2, 1)
    Sm0 = _on_qubit4(SM2, 0); Sm1 = _on_qubit4(SM2, 1)
    Scoup_z = g0z * Sz0 + g1z * Sz1
    Scoup_m = g0m * Sm0 + g1m * Sm1
    H = zeta * np.kron(I16, num) + np.kron(Scoup_z, b + bdag) \
        + np.kron(Scoup_m, bdag) + np.kron(Scoup_m.conj().T, b)
    c = math.sqrt(2.0 * gamma) * np.kron(I16, b)
    D = 16 * nmax
    Id = np.eye(D, dtype=complex)
    L = -1j * (np.kron(Id, H) - np.kron(H.T, Id))
    cdc = c.conj().T @ c
    L = L + np.kron(c.conj(), c) - 0.5 * np.kron(Id, cdc) - 0.5 * np.kron(cdc.T, Id)
    E_full = expm(L * tau)
    rng = np.random.default_rng(2027)
    A = rng.standard_normal((D, D)) + 1j * rng.standard_normal((D, D))
    rho = A @ A.conj().T
    rho = rho / np.trace(rho).real
    ev_full = (E_full @ (rho.T.reshape(-1))).reshape(D, D).T
    E_red, _ = round_superop(nmax, zeta, gamma, g0z, g1z, g0m, g1m, tau)
    ev_red = apply_idle_reduced(E_red, rho, nmax)
    return {"nmax": nmax, "max_abs_err": float(np.max(np.abs(ev_full - ev_red))),
            "full_superop_GB": full_superop_bytes(nmax) / 1e9}


def extraction_gt_check() -> dict:
    """(extX/extZ) both ancillas read their parity deterministically on the parity eigenstates (closed-form)."""
    plus = np.array([1.0, 1.0], dtype=complex) / math.sqrt(2.0)
    minus = np.array([1.0, -1.0], dtype=complex) / math.sqrt(2.0)
    zero = np.array([1.0, 0.0], dtype=complex); one = np.array([0.0, 1.0], dtype=complex)
    UX, UZ = x_parity_unitary_4q(), z_parity_unitary_4q()
    worst_x = 0.0
    # X-parity: |++>,|--> -> +1 -> aX=0 ; |+->,|-+> -> -1 -> aX=1
    for d0v, d1v, exp in [(plus, plus, 0), (plus, minus, 1), (minus, plus, 1), (minus, minus, 0)]:
        v = np.kron(np.kron(np.kron(d0v, d1v), zero), zero)
        out = UX @ np.outer(v, v.conj()) @ UX.conj().T
        p1 = float(np.diag(out).real[AX_BIT == 1].sum())
        worst_x = max(worst_x, abs(p1 - exp))
    worst_z = 0.0
    # Z-parity: |00>,|11> -> +1 -> aZ=0 ; |01>,|10> -> -1 -> aZ=1
    for d0v, d1v, exp in [(zero, zero, 0), (zero, one, 1), (one, zero, 1), (one, one, 0)]:
        v = np.kron(np.kron(np.kron(d0v, d1v), zero), zero)
        out = UZ @ np.outer(v, v.conj()) @ UZ.conj().T
        p1 = float(np.diag(out).real[AZ_BIT == 1].sum())
        worst_z = max(worst_z, abs(p1 - exp))
    return {"worst_err_X": worst_x, "worst_err_Z": worst_z}


def two_qubit_indep_boson_gt(*, nmax, zeta, gamma, g0z, g1z, tau) -> dict:
    """(gtZ) sigma_z sector collective-dephasing GT (v2 form, gm=0): reduced (d0,d1) coherences vs
    0.25 exp(-(Delta s)^2 Gamma_unit). Non-circular independent-boson closed form."""
    E_red, dloc = round_superop(nmax, zeta, gamma, g0z, g1z, 0.0, 0.0, tau)
    plus = np.array([1.0, 1.0], dtype=complex) / math.sqrt(2.0)
    vac = np.zeros(nmax, dtype=complex); vac[0] = 1.0
    psi = np.kron(np.kron(plus, plus), vac)
    rho0 = np.outer(psi, psi.conj())
    rt = (E_red @ (rho0.T.reshape(-1))).reshape(dloc, dloc).T
    rt4 = rt.reshape(4, nmax, 4, nmax)
    rho_dd = np.einsum("aibi->ab", rt4)
    Gamma_unit = gamma_unit_closed(tau, zeta, gamma)
    coup = {0: +1.0, 1: -1.0}
    def s_eig(a, b):
        return g0z * coup[a] + g1z * coup[b]
    worst = 0.0
    for row in range(4):
        a, b = (row >> 1) & 1, row & 1
        for col in range(4):
            ap, bp = (col >> 1) & 1, col & 1
            ds = s_eig(a, b) - s_eig(ap, bp)
            target = 0.25 * math.exp(-(ds * ds) * Gamma_unit)
            worst = max(worst, abs(abs(rho_dd[row, col]) - target))
    return {"Gamma_unit_tau": float(Gamma_unit), "worst_err": float(worst)}


def sigma_minus_emission_gt(*, nmax, zeta, gamma, g, tau, n_t=6) -> dict:
    """(gtT1) single-qubit sigma_minus EMISSION GT: reduced p_e(t) from the GKSL == the EXACT single-excitation-
    sector amplitude ODE. Independent method (Schrodinger amplitude vs GKSL superop), unambiguous.

    1-qubit + mode, H = zeta b^dag b + g(sminus b^dag + splus b), collapse sqrt(2 gamma) b, init |e,0>.
    In the <=1-excitation sector: a=amp|e,0>, c=amp|g,1>; a'=-i g c, c'=-(i zeta + gamma) c - i g a
    (mode amplitude decay gamma from D[sqrt(2 gamma) b]). p_e(t)=|a(t)|^2. The GKSL recycling repopulates the
    DARK |g,0> (uncoupled) so p_e is unaffected => GKSL p_e == |a(t)|^2 exactly.
    """
    b, bdag, num = boson_ops(nmax)
    Sm = SM2; Sp = SM2.conj().T
    H = zeta * np.kron(I2, num) + g * (np.kron(Sm, bdag) + np.kron(Sp, b))
    c = math.sqrt(2.0 * gamma) * np.kron(I2, b)
    d = 2 * nmax
    Id = np.eye(d, dtype=complex)
    L = -1j * (np.kron(Id, H) - np.kron(H.T, Id))
    cdc = c.conj().T @ c
    L = L + np.kron(c.conj(), c) - 0.5 * np.kron(Id, cdc) - 0.5 * np.kron(cdc.T, Id)
    # init |e,0> = |1>_q |0>_mode
    e = np.array([0.0, 1.0], dtype=complex); vac = np.zeros(nmax, dtype=complex); vac[0] = 1.0
    psi = np.kron(e, vac); rho0 = np.outer(psi, psi.conj())
    # 2x2 non-Hermitian amplitude generator: d/dt [a,c]^T = G [a,c]^T
    G = np.array([[0.0, -1j * g], [-1j * g, -(1j * zeta + gamma)]], dtype=complex)
    worst = 0.0; series = []
    for it in range(1, n_t + 1):
        t = tau * it / n_t
        rt = (expm(L * t) @ (rho0.T.reshape(-1))).reshape(d, d).T
        pe_gksl = float(rt.reshape(2, nmax, 2, nmax)[1, :, 1, :].diagonal().sum().real)  # <e,n|rho|e,n> summed
        amp = expm(G * t) @ np.array([1.0, 0.0], dtype=complex)
        pe_ode = float(abs(amp[0]) ** 2)
        worst = max(worst, abs(pe_gksl - pe_ode))
        series.append({"t": t, "pe_gksl": pe_gksl, "pe_ode": pe_ode})
    return {"worst_err": float(worst), "pe_final_gksl": series[-1]["pe_gksl"], "series": series}


def no_bath_sanity(nmax) -> dict:
    """(nobath) bath off -> flat Markov-0 record on BOTH axes, K=0. |++> parity is deterministic each round."""
    r = dual_point(nmax, zeta=1.0, gamma=0.0, g0z=0.0, g1z=0.0, g0m=0.0, g1m=0.0, tau=2.0)
    P1 = {m1: sum(r["P_all"][(m1, m2, m3)] for m2 in M_ALPHABET for m3 in M_ALPHABET) for m1 in M_ALPHABET}
    return {"K_joint": r["K_joint"], "K_X": r["K_X"], "K_Z": r["K_Z"], "M_mem": r["M_mem"], "CMI": r["CMI"],
            "p_max_marginal": max(P1.values())}

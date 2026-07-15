"""Per-unit L0+L1 coverage of the two shared-bath
carrier primitive modules

  * ``error_coupling_simulator.quantum_bath.gksl``       (3 CPU-pure units)
  * ``error_coupling_simulator.quantum_bath.crow_joynt`` (5 CPU-pure units).

Full-coverage program (docs/SIMULATOR.md SS12.3/12.4;
work-list docs/SIMULATOR.md). Both modules are
CPU-pure numpy/scipy (gksl: boson algebra + the SHARED (d0,d1,mode) GKSL Liouvillian +
``scipy.linalg.expm``; crow_joynt: closed-form phase covariance + a 3D Gauss-Hermite average
of the classical sigma_z field through the dual-axis instrument). No torch, no quimb, no cuda
-- so each unit gets the FULL treatment: L0 (100% statement + BOTH arcs of every tracked
branch per unit) + L1 (Hypothesis faithfulness properties) + KILLER teeth. L2 runs through
the current mutation harness.

The 8 units + their L0 branch surface and L1 invariant. NB on the "branch surface":
coverage.py --branch emits NO tracked branch arc for a pure generator/comprehension body, so a
unit that is just a comprehension (or has none of if/for/while/ternary in its OWN body, nested
defs excluded) scores branch 0/0 -- nothing to miss; that is honest, and its faithfulness rests
on the L1 PROPERTY, not on a branch count.

  UNIT (module)                       L0 branch surface                        L1 faithfulness property
  ----                                -----------------                        ------------------------
  boson_ops (gksl)                    `for n in range(1,nmax)` loop arc        b_dag == b.conj().T (creation =
                                      (nmax>=2 enters body; nmax==1 skips)     adjoint of annihilation); num=b^dag b
  build_shared_bath_liouvillian       none tracked (straight-line; 0/0)        L is a valid GKSL generator:
   (gksl)                                                                      exp(L*tau) is trace/Herm preserving
  round_superop (gksl)                none tracked (straight-line; 0/0)        exp(L*tau) is CPTP (TP to ~1e-9,
                                                                               Hermiticity-preserving, CP via Choi)
  gamma_unit_closed (crow_joynt)      none tracked (straight-line; 0/0)        Gamma_unit(0)=0; matches the numerical
                                                                               _gamma_of_t cross-check to ~1e-9;
                                                                               pins the certified value 1.32329713
  sigma_offdiag_closed (crow_joynt)   none tracked (straight-line; 0/0)        real-valued; matches build_sigma's
                                                                               off-diagonal; pins certified values
  build_sigma (crow_joynt)            `for r`/`for s` loops + the `if r==s`    symmetric Hermitian PSD (eigvals>=0);
                                      ternary (r==s diag arc AND r!=s          diag=2*Gamma_unit; Toeplitz off-diag
                                      off-diag arc)                            = sigma_offdiag_closed(|r-s|)
  field_null_dual_P_all (crow_joynt)  P_all/P_skip dict comprehensions (0/0    P_all sums to 1 (trace-preserving
                                      tracked) + the i/j/k Gauss-Hermite       instrument); K_joint>=0; K_Z ~ 0
                                      loops + the m1/m2/m3 loops (loop arcs);   (sigma_z field is Z-inert); all P>=0
                                      nested rot/idle_r defs are separate
  field_null_point (crow_joynt)       none tracked (straight-line; 0/0)        norm ~ 1; K_joint>=0; K_Z ~ 0;
                                                                               returns the full record dict

CLOSED-FORM PINS (gamma_unit_closed / sigma_offdiag_closed / build_sigma). These reproduce the
CERTIFIED ground-truth numbers already asserted in tests/test_quantum_bath.py
(test_crow_joynt_covariance_closed_forms): gamma_unit_closed(2,1,0.15)==1.32329713,
build_sigma(3,2,1,0.15) == the Scout-A matrix, PSD, diag==2*Gamma_unit. We re-pin them here at
the unit granularity AND assert their structural properties (real-valued, symmetric, Toeplitz,
PSD) so a closed-form regression fails at this level too.

TP/PSD SIGN CAVEAT. round_superop's TP is verified in the vec convention the module DECLARES
(column-stacking vec(B)=B.T.reshape(-1), gksl.py line 7): rho -> unvec(E @ vec(rho)); the L0/L1
apply-helper uses exactly that convention, so a convention mismatch would surface as a spurious
TP failure (it does not). gamma_unit_closed is NOT asserted monotone or sign-definite in tau (it
is an oscillatory-times-decaying integral -- Gamma_unit(5)<Gamma_unit(3)); only Gamma_unit(0)=0,
the numerical cross-check, and the certified pins are claimed. sigma_offdiag_closed likewise
oscillates in m (offdiag(5)<0<offdiag(10)); no monotone-decay claim -- exact pins only.

Two-sided teeth (KILLER). The load-bearing L1 asserts (round_superop CPTP/trace-preservation,
build_sigma PSD, field_null_dual_P_all norm==1) are each shown DISCRIMINATING: an inlined
sabotaged variant VIOLATES the property in the claimed direction on a crafted input, verified
here (feedback-devious-tests-killer-standard). The sabotage directions were confirmed by CPU
probe before wiring: dropping the GKSL anticommutator dissipator terms inflates the trace to
~1.35 (breaks TP); halving the covariance diagonal (dropping the factor of 2) drives min-eig to
~-0.36 (breaks PSD); dropping the Gauss-Hermite /sqrt(2pi) weight normalization inflates the
3D weight sum to ~15.75 (breaks norm==1).
"""
from __future__ import annotations

import math
import os

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from scipy.linalg import expm

from error_coupling_simulator.quantum_bath import crow_joynt as cj
from error_coupling_simulator.quantum_bath import gksl

# canonical study params (the certified ground-truth point in test_quantum_bath.py).
ZETA, GAMMA, TAU = 1.0, 0.15, 2.0


# --------------------------------------------------------------------------- #
# shared helpers (deterministic; the batch's fixtures, NOT ad-hoc)            #
# --------------------------------------------------------------------------- #
def _apply_super(E: np.ndarray, rho: np.ndarray, D: int) -> np.ndarray:
    """Apply the round superoperator in the module's DECLARED column-stacking convention
    (vec(B)=B.T.reshape(-1), gksl.py line 7): rho -> unvec(E @ vec(rho))."""
    return (E @ (rho.T.reshape(-1))).reshape(D, D).T


def _random_dm(D: int, seed: int) -> np.ndarray:
    """A random full-rank density matrix (Hermitian PSD, unit trace) for TP/CP probes."""
    rng = np.random.default_rng(seed)
    A = rng.standard_normal((D, D)) + 1j * rng.standard_normal((D, D))
    rho = A @ A.conj().T
    return rho / np.trace(rho)


def _choi(E: np.ndarray, D: int) -> np.ndarray:
    """Choi matrix of the superop E (in the module's vec convention): sum_ij E(|i><j|) (x) |i><j|.
    CP <=> Choi is PSD."""
    C = np.zeros((D * D, D * D), dtype=complex)
    for i in range(D):
        for j in range(D):
            Eij = np.zeros((D, D), dtype=complex)
            Eij[i, j] = 1.0
            C += np.kron(_apply_super(E, Eij, D), Eij)
    return (C + C.conj().T) / 2.0


# --- emission-physics observables on the reduced (d0,d1,mode) DM (dim 4*nmax) ------------- #
# The reduced-space basis is kron(data4, mode_nmax): flat index = data*nmax + mode, with
# data in 0..3 = (d0,d1) MSB-first and mode in 0..nmax-1. These read the PHYSICAL effect of
# the two emission channels the module builds: (i) the mode-loss collapse c = sqrt(2*gamma)*b
# (excited-mode population decay), (ii) the sigma_minus qubit->mode JC coupling (energy
# transfer OUT of an excited data qubit INTO the mode). A vacuous CPTP-only test cannot see
# either -- dropping them keeps exp(L*tau) CPTP -- so these give the emission its teeth.
def _mode_excited_pop(rho: np.ndarray, nmax: int) -> float:
    """Population of the mode-|1> level, summed over the 4 data configs (reduced (d0,d1,mode))."""
    return float(sum(rho[d * nmax + 1, d * nmax + 1].real for d in range(4)))


def _d0_excited_pop(rho: np.ndarray, nmax: int) -> float:
    """Population of data-qubit d0 = |1> (d0 is the MSB of the 4-dim data block), any d1/mode."""
    tot = 0.0
    for data in range(4):
        if (data >> 1) & 1 == 1:  # d0 excited
            for m in range(nmax):
                tot += rho[data * nmax + m, data * nmax + m].real
    return float(tot)


def _reduced_dm_data_mode(nmax: int, data_idx: int, mode_idx: int) -> np.ndarray:
    """Pure |data,mode><data,mode| on the reduced (d0,d1,mode) space (dim 4*nmax)."""
    dloc = 4 * nmax
    rho = np.zeros((dloc, dloc), dtype=complex)
    i = data_idx * nmax + mode_idx
    rho[i, i] = 1.0
    return rho


def _ref_shared_bath_liouvillian(nmax, zeta, gamma, g0z, g1z, g0m, g1m):
    """INDEPENDENT from-scratch reference for build_shared_bath_liouvillian: the SAME shared-bath
    GKSL generator, but built without ANY gksl helper -- ladder ops via np.diag(sqrt(.),1), Pauli
    matrices spelled out, every sign written explicitly. Reproduces the module Liouvillian to
    machine zero when correct, and DIVERGES under a sign flip in any coupling / Hamiltonian /
    evolution term (verified in test_KILLER_liouvillian_signs_*). H, jump operators, and the
    dissipator follow the module's docstring:
      H = zeta b^dag b + (g0z sz0 + g1z sz1)(b+b^dag) + [(g0m sm0 + g1m sm1) b^dag + h.c.]
      c = sqrt(2 gamma) b ;  L = -i[H,.] + c(.)c^dag - 1/2{c^dag c, .}   (column-stacking vec)."""
    b = np.diag(np.sqrt(np.arange(1, nmax)), 1).astype(complex)
    bdag = b.conj().T
    num = bdag @ b
    sz = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
    sm = np.array([[0.0, 1.0], [0.0, 0.0]], dtype=complex)
    eye2 = np.eye(2, dtype=complex)
    Sz0, Sz1 = np.kron(sz, eye2), np.kron(eye2, sz)
    Sm0, Sm1 = np.kron(sm, eye2), np.kron(eye2, sm)
    Scoup_z = g0z * Sz0 + g1z * Sz1
    Scoup_m = g0m * Sm0 + g1m * Sm1
    H = zeta * np.kron(np.eye(4, dtype=complex), num)
    H = H + np.kron(Scoup_z, b + bdag)
    H = H + np.kron(Scoup_m, bdag) + np.kron(Scoup_m.conj().T, b)
    c = math.sqrt(2.0 * gamma) * np.kron(np.eye(4, dtype=complex), b)
    dloc = 4 * nmax
    Id = np.eye(dloc, dtype=complex)
    L = -1j * (np.kron(Id, H) - np.kron(H.T, Id))
    cdc = c.conj().T @ c
    L = L + np.kron(c.conj(), c) - 0.5 * np.kron(Id, cdc) - 0.5 * np.kron(cdc.T, Id)
    return L, dloc


# --- INDEPENDENT from-scratch reconstruction of the crow_joynt field-null record ---------- #
# NOT a call into field_null_dual_P_all / dual_extract / carrier: an explicit 2-data-qubit DM
# simulation of the classical sigma_z field pushed through PROJECTIVE X-parity + Z-parity
# measurements (X0X1, Z0Z1 commute), Gaussian-averaged by the SAME 3D Gauss-Hermite rule.
# This reproduces the module's (P_all, P_skip) -- hence K_X / K_joint -- to machine zero when
# the module is correct, and DIVERGES the moment the field, its covariance, or the instrument
# is wrong (verified in test_KILLER_field_null_KX_*). build_sigma IS reused (it is a separately
# closed-form-pinned unit); everything downstream of it is reconstructed from first principles.
def _recon_field_null(zeta, gamma, g0z, g1z, tau, n_gh):
    from numpy.polynomial.hermite_e import hermegauss

    from error_coupling_simulator.quantum_bath.observables import M_ALPHABET

    R = 3
    Zeig = np.array([1.0, -1.0])
    z0 = np.array([Zeig[(i >> 1) & 1] for i in range(4)])   # Z on d0 (MSB of the 4-dim data)
    z1 = np.array([Zeig[i & 1] for i in range(4)])          # Z on d1
    sz = g0z * z0 + g1z * z1                                 # diagonal sigma_z generator (4-dim)
    plus = np.array([1.0, 1.0], dtype=complex) / math.sqrt(2.0)
    psi0 = np.kron(plus, plus)
    rho0 = np.outer(psi0, psi0.conj())                      # |++><++|  (4x4)
    Hd = np.array([[1.0, 1.0], [1.0, -1.0]], dtype=complex) / math.sqrt(2.0)
    HH = np.kron(Hd, Hd)

    def zpar_proj(par):                                     # Z0Z1 parity projector (0 even / 1 odd)
        P = np.zeros((4, 4), dtype=complex)
        for i in range(4):
            if (((i >> 1) & 1) ^ (i & 1)) == par:
                P[i, i] = 1.0
        return P

    def xpar_proj(par):                                    # X0X1 parity = Z-parity in the H-rotated basis
        return HH @ zpar_proj(par) @ HH.conj().T

    Sigma = cj.build_sigma(R, tau, zeta, gamma)
    Lchol = np.linalg.cholesky(Sigma)
    x, w = hermegauss(n_gh)
    wn = w / math.sqrt(2.0 * math.pi)

    def rot(phi):
        d = np.exp(-1j * sz * phi)
        return np.outer(d, d.conj())                       # diagonal unitary conjugation as a mask

    def measure(rho, m):
        sX, sZ = m
        Px = xpar_proj(sX)
        r = Px @ rho @ Px.conj().T
        Pz = zpar_proj(sZ)
        return Pz @ r @ Pz.conj().T

    P_all = {(m1, m2, m3): 0.0 for m1 in M_ALPHABET for m2 in M_ALPHABET for m3 in M_ALPHABET}
    P_skip = {(m1, m3): 0.0 for m1 in M_ALPHABET for m3 in M_ALPHABET}
    for i in range(n_gh):
        for j in range(n_gh):
            for k in range(n_gh):
                phi = Lchol @ np.array([x[i], x[j], x[k]])
                weight = wn[i] * wn[j] * wn[k]
                r1 = rot(phi[0]) * rho0
                for m1 in M_ALPHABET:
                    a1 = measure(r1, m1)
                    r2 = rot(phi[1]) * a1
                    for m2 in M_ALPHABET:
                        a2 = measure(r2, m2)
                        r3 = rot(phi[2]) * a2
                        for m3 in M_ALPHABET:
                            a3 = measure(r3, m3)
                            P_all[(m1, m2, m3)] += weight * float(np.trace(a3).real)
                    r_ev = rot(phi[2]) * (rot(phi[1]) * a1)
                    for m3 in M_ALPHABET:
                        a3 = measure(r_ev, m3)
                        P_skip[(m1, m3)] += weight * float(np.trace(a3).real)
    return P_all, P_skip


# NB (review fix): the field-null record is pinned by EQUALITY to the independent
# _recon_field_null reconstruction AT THE SAME n_gh -- NOT to a hardcoded absolute constant.
# The tests run at a cheap n_gh=2, which is a TRUNCATED Gauss-Hermite quadrature (K_X~0.11),
# NOT the converged physical value (n_gh>=24 -> K_X~3.3e-4, matching crow_joynt.py's docstring).
# Pinning 0.11 as "certified physical" was a truncation artifact (332x the physical value); the
# honest, n_gh-independent faithfulness check is module==independent-recon + positivity.


# =========================================================================== #
# L0 -- per-unit statement + branch coverage (explicit, crafted inputs)       #
# =========================================================================== #
def test_L0_boson_ops_covers_loop_body_and_empty_loop():
    # nmax>=2 ENTERS the `for n in range(1,nmax)` body (fills the superdiagonal);
    b, bdag, num = gksl.boson_ops(3)
    assert b.shape == (3, 3)
    # annihilation lowers |n> -> sqrt(n)|n-1>: b[n-1,n]=sqrt(n)
    assert b[0, 1] == pytest.approx(math.sqrt(1))
    assert b[1, 2] == pytest.approx(math.sqrt(2))
    assert np.allclose(bdag, b.conj().T)          # creation = adjoint of annihilation
    assert np.allclose(num, bdag @ b)             # number = b^dag b
    # nmax==1 SKIPS the loop body (range(1,1) is empty) -> all-zero 1x1 operators.
    b1, bdag1, num1 = gksl.boson_ops(1)
    assert b1.shape == (1, 1) and np.allclose(b1, 0.0)
    assert np.allclose(bdag1, 0.0) and np.allclose(num1, 0.0)


def test_L0_build_shared_bath_liouvillian_runs_and_shapes():
    # straight-line body (no branch arcs): exercise every statement, check the shape contract.
    L, dloc = gksl.build_shared_bath_liouvillian(2, ZETA, GAMMA, 0.5, 0.5, 0.35, 0.35)
    assert dloc == 4 * 2                          # reduced (d0,d1,mode) dim = 4*nmax
    assert L.shape == (dloc * dloc, dloc * dloc)  # Liouvillian on vec-space
    # a GKSL generator is trace-annihilating on any input: vec(I)-covector . L = 0 in the
    # module's column-stacking convention -> exp(L*t) is trace preserving (checked in L1).
    assert np.all(np.isfinite(L))

    # ---- EMISSION CHANNEL 1: the mode-loss collapse c = sqrt(2*gamma)*b -----------------
    # With EVERY qubit-mode coupling switched off (g*=0), the mode decouples from the data
    # and the ONLY dynamics is pure amplitude damping of the bosonic mode at rate 2*gamma.
    # Independent closed form (Lindblad amplitude damping): the mode-|1> population decays
    # EXACTLY as exp(-2*gamma*tau). This pins BOTH the collapse operator's presence (drop the
    # dissipator -> no decay, pop stays 1) AND its sqrt(2*gamma) prefactor (a sqrt(gamma)
    # typo -> exp(-gamma*tau) = 0.741, not 0.549) -- neither is visible to a CPTP-only check.
    nmax = 2
    L0, d0 = gksl.build_shared_bath_liouvillian(nmax, ZETA, GAMMA, 0.0, 0.0, 0.0, 0.0)
    E0 = expm(L0 * TAU)
    rho_mode1 = _reduced_dm_data_mode(nmax, data_idx=0, mode_idx=1)  # |00>_data |1>_mode
    out0 = _apply_super(E0, rho_mode1, d0)
    assert _mode_excited_pop(out0, nmax) == pytest.approx(math.exp(-2.0 * GAMMA * TAU), abs=1e-9)

    # ---- EMISSION CHANNEL 2: the sigma_minus qubit->mode JC coupling (g0m/g1m) -----------
    # Prepare an EXCITED data qubit d0 (|10>_data) with the mode in vacuum. The sigma_minus
    # JC term (g0m sminus0)(b^dag) + h.c. transfers the qubit excitation INTO the mode, so
    # after tau the mode gains |1> population and d0 LOSES excitation. With the emission term
    # dropped the qubit is frozen (mode stays empty, d0 stays fully excited) -- so a positive
    # transfer is a field-DEPENDENT witness of the sigma_minus coupling. gamma small so the
    # transferred quantum is not immediately damped away.
    Lm, dm = gksl.build_shared_bath_liouvillian(nmax, ZETA, 0.01, 0.0, 0.0, 0.4, 0.0)
    Em = expm(Lm * TAU)
    rho_q = _reduced_dm_data_mode(nmax, data_idx=2, mode_idx=0)      # |10>_data |0>_mode
    outm = _apply_super(Em, rho_q, dm)
    assert _mode_excited_pop(outm, nmax) > 0.3        # excitation transferred qubit -> mode
    assert _d0_excited_pop(outm, nmax) < 0.7          # d0 lost excitation (was exactly 1.0)
    assert _d0_excited_pop(rho_q, nmax) == pytest.approx(1.0, abs=1e-12)  # sanity: started fully excited


def test_L0_round_superop_runs_and_is_finite():
    # straight-line: builds L then returns expm(L*tau). Exercise the whole body.
    E, dloc = gksl.round_superop(2, ZETA, GAMMA, 0.5, 0.5, 0.35, 0.35, TAU)
    assert dloc == 8 and E.shape == (64, 64)
    assert np.all(np.isfinite(E))
    # sanity: the identity round (tau=0) is the identity superoperator.
    E0, _ = gksl.round_superop(2, ZETA, GAMMA, 0.5, 0.5, 0.35, 0.35, 0.0)
    assert np.allclose(E0, np.eye(64))

    # FAITHFULNESS PIN (kills sign/coupling flips a CPTP-only check cannot see): evolve a data
    # superposition |++> with ALL FOUR couplings nonzero and pin the evolved reduced DM against
    # an INDEPENDENT from-scratch reference Liouvillian (built with NO gksl helper). A flipped
    # sign on Scoup_z, Scoup_m, the dephasing term, or the -1j evolution moves these elements by
    # ~0.1-0.3 (verified in test_KILLER_liouvillian_signs_*); the correct build matches to ~1e-9.
    E2, d2 = gksl.round_superop(2, ZETA, GAMMA, 0.5, 0.3, 0.35, 0.25, TAU)
    plus = np.array([1.0, 1.0], dtype=complex) / math.sqrt(2.0)
    psi = np.kron(np.kron(plus, plus), np.array([1.0, 0.0], dtype=complex))  # |++>_data |0>_mode
    rho0 = np.outer(psi, psi.conj())
    out = _apply_super(E2, rho0, d2)
    Lref, dref = _ref_shared_bath_liouvillian(2, ZETA, GAMMA, 0.5, 0.3, 0.35, 0.25)
    out_ref = _apply_super(expm(Lref * TAU), rho0, dref)
    assert np.max(np.abs(out - out_ref)) < 1e-8      # module == independent from-scratch GT
    # spot-pin a coherence and a population that the sign flips move materially.
    assert out[0, 2] == pytest.approx(0.0786463212 + 0.1101208272j, abs=1e-6)
    assert out[0, 0].real == pytest.approx(0.2417600517, abs=1e-6)


def test_L0_gamma_unit_closed_runs_and_pins():
    # straight-line closed form. Pin the certified value + the tau=0 boundary.
    assert cj.gamma_unit_closed(TAU, ZETA, GAMMA) == pytest.approx(1.32329713, abs=1e-6)
    assert cj.gamma_unit_closed(0.0, ZETA, GAMMA) == pytest.approx(0.0, abs=1e-12)
    # the value is a plain float (the .real of I1 was taken inside)
    assert isinstance(cj.gamma_unit_closed(TAU, ZETA, GAMMA), float)


def test_L0_sigma_offdiag_closed_runs_and_pins():
    # straight-line closed form; pins the certified off-diagonal values (Scout-A matrix).
    assert cj.sigma_offdiag_closed(1, TAU, ZETA, GAMMA) == pytest.approx(-0.670271, abs=1e-5)
    assert cj.sigma_offdiag_closed(2, TAU, ZETA, GAMMA) == pytest.approx(-1.146587, abs=1e-5)
    assert isinstance(cj.sigma_offdiag_closed(1, TAU, ZETA, GAMMA), float)


def test_L0_build_sigma_covers_both_ternary_arcs():
    # R>=2 visits BOTH the r==s diagonal arc AND the r!=s off-diagonal arc of the ternary.
    S = cj.build_sigma(3, TAU, ZETA, GAMMA)
    assert S.shape == (3, 3)
    gu = cj.gamma_unit_closed(TAU, ZETA, GAMMA)
    # diagonal arc (r==s): 2*Gamma_unit
    assert S[0, 0] == pytest.approx(2.0 * gu, abs=1e-9)
    assert S[1, 1] == pytest.approx(2.0 * gu, abs=1e-9)
    # off-diagonal arc (r!=s): sigma_offdiag_closed(|r-s|)
    assert S[0, 1] == pytest.approx(cj.sigma_offdiag_closed(1, TAU, ZETA, GAMMA), abs=1e-9)
    assert S[0, 2] == pytest.approx(cj.sigma_offdiag_closed(2, TAU, ZETA, GAMMA), abs=1e-9)
    # certified Scout-A matrix (matches test_quantum_bath.py)
    scout = np.array([[2.646594, -0.670271, -1.146587],
                      [-0.670271, 2.646594, -0.670271],
                      [-1.146587, -0.670271, 2.646594]])
    assert np.max(np.abs(S - scout)) < 1e-5
    # R==1 hits ONLY the r==s diagonal arc (the off-diag arc is not taken, but both arcs of
    # the ternary DECISION are exercised across the two calls).
    S1 = cj.build_sigma(1, TAU, ZETA, GAMMA)
    assert S1.shape == (1, 1) and S1[0, 0] == pytest.approx(2.0 * gu, abs=1e-9)


def test_L0_field_null_dual_P_all_runs_and_is_normalized():
    # cheap n_gh=2 (2^3=8 Gauss-Hermite nodes). Exercises the i/j/k + m1/m2/m3 loops and the
    # P_all/P_skip comprehension bodies (comprehensions score 0/0 branch -- honest).
    P_all, P_skip = cj.field_null_dual_P_all(zeta=ZETA, gamma=GAMMA, g0z=0.5, g1z=0.5,
                                             tau=TAU, n_gh=2)
    assert len(P_all) == 64 and len(P_skip) == 16
    # norm==1 alone is VACUOUS (holds for ANY trace-preserving instrument, incl. a dropped
    # field). The DISCRIMINATING content is the full field-null record MATCHING an INDEPENDENT
    # from-scratch reconstruction (2-qubit DM + projective parity measures, NOT dual_extract).
    Pr, Psr = _recon_field_null(ZETA, GAMMA, 0.5, 0.5, TAU, 2)
    assert max(abs(P_all[k] - Pr[k]) for k in P_all) < 1e-12      # joint record == independent GT
    assert max(abs(P_skip[k] - Psr[k]) for k in P_skip) < 1e-12   # skip-record == independent GT
    # and the record's X-side Kolmogorov-violation MATCHES the independent reconstruction (the
    # honest, n_gh-independent faithfulness content -- NO absolute constant, since n_gh=2 is a
    # truncated quadrature). A dropped/mis-scaled field or wrong covariance breaks the match.
    PaX, PsX = cj.project_axis(P_all, 0), cj.project_axis(P_skip, 0)
    PrX, PsrX = cj.project_axis(Pr, 0), cj.project_axis(Psr, 0)
    assert cj.K_stat_binary(PaX, PsX) == pytest.approx(cj.K_stat_binary(PrX, PsrX), abs=1e-9)
    assert cj.K_stat_joint(P_all, P_skip) == pytest.approx(cj.K_stat_joint(Pr, Psr), abs=1e-9)
    assert cj.K_stat_binary(PaX, PsX) > 1e-6      # positive + field-ON (holds at converged n_gh too)
    # all outcome probabilities are non-negative (a genuine distribution).
    assert min(P_all.values()) >= -1e-12
    assert min(P_skip.values()) >= -1e-12
    # trace preservation + P_skip normalization (sanity, non-discriminating on their own).
    assert sum(P_all.values()) == pytest.approx(1.0, abs=1e-6)
    assert sum(P_skip.values()) == pytest.approx(1.0, abs=1e-6)


def test_L0_field_null_point_runs_and_returns_record():
    # straight-line wrapper: build the null then read the record statistics.
    out = cj.field_null_point(zeta=ZETA, gamma=GAMMA, g0z=0.5, g1z=0.5, tau=TAU, n_gh=2)
    assert out["norm"] == pytest.approx(1.0, abs=1e-6)
    for key in ("K_joint", "K_X", "K_Z", "M_mem", "CMI", "P_all", "P_skip", "norm"):
        assert key in out
    # DISCRIMINATING: the wrapper's field-DEPENDENT record MATCHES the independent recon (no
    # absolute-value pin -- n_gh=2 is truncated, not converged). A vacuous K_joint>=0 (sum-of-abs)
    # or K_Z<1e-6 (Z-inertness, structural) survives dropping the field; the recon match does not.
    Pr, Psr = _recon_field_null(ZETA, GAMMA, 0.5, 0.5, TAU, 2)
    PrX, PsrX = cj.project_axis(Pr, 0), cj.project_axis(Psr, 0)
    assert out["K_X"] == pytest.approx(cj.K_stat_binary(PrX, PsrX), abs=1e-9)
    assert out["K_joint"] == pytest.approx(cj.K_stat_joint(Pr, Psr), abs=1e-9)
    assert out["K_X"] > 1e-6                     # positive + field-ON (holds at converged n_gh too)
    # structural sanity only (NOT the faithfulness property): a sigma_z field commutes with
    # the Z-parity, so the Z-axis marginal carries no Kolmogorov violation -- this holds for
    # ANY sigma_z field strength/covariance and is NOT a discriminating check.
    assert out["K_Z"] < 1e-6


@pytest.mark.skipif(os.environ.get("ECS_MUTATION_SKIP_SLOW") == "1",
                    reason="slow converged n_gh=24 physics pin (~20s); runs in the coverage "
                           "gate, skipped under mutation for speed (the functions it exercises "
                           "are already killed by the fast n_gh=2 recon-match + closed-form pins)")
def test_field_null_KX_converges_to_the_PHYSICAL_value():
    # What SHOULD field_null_point produce? The cheap n_gh=2 tests above verify the
    # IMPLEMENTATION (module == independent recon) but NOT physical convergence -- n_gh=2 gives
    # K_X~0.11, a Gauss-Hermite TRUNCATION artifact. This ONE converged call pins the CORRECT
    # NUMERICAL REGRESSION: K_X -> 3.3195e-4 at n_gh=24 (Δ to n_gh=28 is 5e-9).
    # The inherited scientific interpretation remains pending the current formula audit.
    out = cj.field_null_point(zeta=ZETA, gamma=GAMMA, g0z=0.5, g1z=0.5, tau=TAU, n_gh=24)
    kx = out["K_X"]
    assert kx == pytest.approx(3.3195e-4, abs=1e-6)   # the CONVERGED physical value (not 0.11)
    assert kx < 1e-3                                    # NOT the n_gh=2 truncation artifact
    assert len(out["P_all"]) == 64 and len(out["P_skip"]) == 16


# =========================================================================== #
# L1 -- Hypothesis faithfulness properties                                     #
#   cheap linear-algebra units (boson_ops, closed forms, build_sigma): generous  #
#   expensive DM/dynamics units (round_superop, field_null): modest examples    #
# =========================================================================== #
@st.composite
def bath_params(draw):
    """Physical bath params in a benign, well-conditioned range (gamma>0 for a real GKSL)."""
    zeta = draw(st.floats(min_value=0.1, max_value=3.0))
    gamma = draw(st.floats(min_value=0.05, max_value=2.0))
    g0z = draw(st.floats(min_value=-0.6, max_value=0.6))
    g1z = draw(st.floats(min_value=-0.6, max_value=0.6))
    g0m = draw(st.floats(min_value=-0.4, max_value=0.4))
    g1m = draw(st.floats(min_value=-0.4, max_value=0.4))
    tau = draw(st.floats(min_value=0.2, max_value=3.0))
    return zeta, gamma, g0z, g1z, g0m, g1m, tau


@settings(max_examples=200, deadline=None)
@given(st.integers(min_value=1, max_value=6))
def test_L1_boson_ops_is_adjoint_pair_and_number(nmax):
    """b_dag == b.conj().T (creation is the adjoint of annihilation) and num == b^dag b -- an
    ACTUAL algebraic identity for the harmonic-oscillator ladder operators (any nmax)."""
    b, bdag, num = gksl.boson_ops(nmax)
    assert np.allclose(bdag, b.conj().T)
    assert np.allclose(num, bdag @ b)
    # the number operator is diagonal with entries 0,1,...,nmax-1
    assert np.allclose(np.diag(num).real, np.arange(nmax))
    # b is strictly upper-triangular (raises index by one) -> nilpotent
    assert np.allclose(np.tril(b), 0.0)


@settings(max_examples=250, deadline=None)
@given(bath_params())
def test_L1_gamma_unit_matches_numerical_crosscheck(p):
    """gamma_unit_closed(tau,zeta,gamma) == the numerical _gamma_of_t(tau,zeta,gamma,g=1) to
    ~1e-6 -- the closed form reproduces the integral it claims to be (INDEPENDENT numerical GT)."""
    zeta, gamma, _g0z, _g1z, _g0m, _g1m, tau = p
    closed = cj.gamma_unit_closed(tau, zeta, gamma)
    numer = cj._gamma_of_t(tau, zeta, gamma, 1.0)
    assert closed == pytest.approx(numer, abs=1e-5, rel=1e-5)
    assert math.isfinite(closed)


@settings(max_examples=250, deadline=None)
@given(bath_params())
def test_L1_sigma_offdiag_is_real_and_finite(p):
    """sigma_offdiag_closed returns a finite real float for any m>=1 (the .real was taken)."""
    zeta, gamma, _g0z, _g1z, _g0m, _g1m, tau = p
    for m in (1, 2, 3, 5):
        v = cj.sigma_offdiag_closed(m, tau, zeta, gamma)
        assert isinstance(v, float) and math.isfinite(v)


@settings(max_examples=120, deadline=None)
@given(st.integers(min_value=1, max_value=6), bath_params())
def test_L1_build_sigma_is_symmetric_psd_toeplitz(R, p):
    """build_sigma is symmetric Hermitian PSD (eigvals >= 0), diag == 2*Gamma_unit, and Toeplitz
    (S[r,s] depends only on |r-s|) -- it is a valid Gaussian phase covariance (an ACTUAL theorem:
    it matches a symmetrized two-time correlation, which is a PSD kernel)."""
    zeta, gamma, _g0z, _g1z, _g0m, _g1m, tau = p
    S = cj.build_sigma(R, tau, zeta, gamma)
    assert S.shape == (R, R)
    assert np.allclose(S, S.T)                              # symmetric (real => Hermitian)
    assert np.linalg.eigvalsh(S).min() >= -1e-9            # PSD
    gu = cj.gamma_unit_closed(tau, zeta, gamma)
    assert np.allclose(np.diag(S), 2.0 * gu)               # diagonal = 2*Gamma_unit
    # Toeplitz: every entry depends only on |r-s|
    for r in range(R):
        for s in range(R):
            if r != s:
                assert S[r, s] == pytest.approx(
                    cj.sigma_offdiag_closed(abs(r - s), tau, zeta, gamma), abs=1e-9)


@settings(max_examples=25, deadline=None)
@given(bath_params())
def test_L1_round_superop_is_cptp(p):
    """exp(L*tau) is a CPTP map: trace-preserving (~1e-9), Hermiticity-preserving, and completely
    positive (Choi PSD). This is the DEFINING faithfulness invariant of a GKSL round -- L being a
    Lindblad generator makes exp(L*tau) a quantum channel. nmax=2 (D=8) keeps the 64x64 Choi cheap."""
    zeta, gamma, g0z, g1z, g0m, g1m, tau = p
    E, D = gksl.round_superop(2, zeta, gamma, g0z, g1z, g0m, g1m, tau)
    # trace preservation on a random density matrix
    rho = _random_dm(D, seed=0)
    out = _apply_super(E, rho, D)
    assert abs(np.trace(out) - 1.0) < 1e-9                  # TP
    assert np.allclose(out, out.conj().T, atol=1e-9)        # Hermiticity-preserving
    # complete positivity: Choi matrix is PSD (allow tiny negative fp noise)
    assert np.linalg.eigvalsh(_choi(E, D)).min() >= -1e-8   # CP


@settings(max_examples=8, deadline=None)
@given(st.floats(min_value=0.2, max_value=2.5),   # zeta
       st.floats(min_value=0.05, max_value=1.5),  # gamma
       st.floats(min_value=-0.6, max_value=0.6),  # g0z
       st.floats(min_value=-0.6, max_value=0.6),  # g1z
       st.floats(min_value=0.5, max_value=3.0))   # tau
def test_L1_field_null_is_normalized_and_z_inert(zeta, gamma, g0z, g1z, tau):
    """The classical sigma_z field pushed through the dual-axis instrument REPRODUCES an
    INDEPENDENT from-scratch reconstruction of the record (2-qubit DM + projective X/Z parity
    measures) -- for EVERY drawn (zeta,gamma,g0z,g1z,tau). This is the actual faithfulness
    property: it pins the whole field-dependent joint distribution, so a wrong field/covariance/
    instrument fails on SOME draw. norm==1 and K_Z~0 are kept only as structural sanity (both
    survive dropping the field, hence non-discriminating). n_gh=2 keeps each call ~0.02s."""
    P_all, P_skip = cj.field_null_dual_P_all(zeta=zeta, gamma=gamma, g0z=g0z, g1z=g1z,
                                             tau=tau, n_gh=2)
    Pr, Psr = _recon_field_null(zeta, gamma, g0z, g1z, tau, 2)
    assert max(abs(P_all[k] - Pr[k]) for k in P_all) < 1e-10        # joint == independent GT
    assert max(abs(P_skip[k] - Psr[k]) for k in P_skip) < 1e-10     # skip == independent GT
    # K_X on the reconstruction matches the module's K_X (field-dependent record statistic).
    PaX, PsX = cj.project_axis(P_all, 0), cj.project_axis(P_skip, 0)
    PrX, PsrX = cj.project_axis(Pr, 0), cj.project_axis(Psr, 0)
    assert cj.K_stat_binary(PaX, PsX) == pytest.approx(cj.K_stat_binary(PrX, PsrX), abs=1e-9)
    assert min(P_all.values()) >= -1e-9
    out = cj.field_null_point(zeta=zeta, gamma=gamma, g0z=g0z, g1z=g1z, tau=tau, n_gh=2)
    assert out["norm"] == pytest.approx(1.0, abs=1e-6)              # structural sanity
    assert out["K_joint"] >= 0.0                                   # structural sanity
    assert out["K_Z"] < 1e-6                                       # structural: sigma_z is Z-inert


# =========================================================================== #
# KILLER (Side-A teeth) -- prove the load-bearing asserts DISCRIMINATE          #
# =========================================================================== #
def _build_L_no_dissipator(nmax, zeta, gamma, g0z, g1z, g0m, g1m):
    """Sabotage build_shared_bath_liouvillian: DROP the -0.5{c^dag c, .} anticommutator terms of
    the GKSL dissipator (keep only the jump term c(.)c^dag). This is NOT trace-preserving -- the
    generator no longer annihilates the trace, so exp(L*tau) inflates tr(rho) away from 1."""
    b, bdag, num = gksl.boson_ops(nmax)
    Sz0 = np.kron(gksl.SZ2, gksl.I2); Sz1 = np.kron(gksl.I2, gksl.SZ2)
    Sm0 = np.kron(gksl.SM2, gksl.I2); Sm1 = np.kron(gksl.I2, gksl.SM2)
    Scoup_z = g0z * Sz0 + g1z * Sz1
    Scoup_m = g0m * Sm0 + g1m * Sm1
    H = zeta * np.kron(np.eye(4, dtype=complex), num)
    H = H + np.kron(Scoup_z, b + bdag)
    H = H + np.kron(Scoup_m, bdag) + np.kron(Scoup_m.conj().T, b)
    c = math.sqrt(2.0 * gamma) * np.kron(np.eye(4, dtype=complex), b)
    dloc = 4 * nmax
    Id = np.eye(dloc, dtype=complex)
    L = -1j * (np.kron(Id, H) - np.kron(H.T, Id))
    L = L + np.kron(c.conj(), c)              # <-- BUG: dropped -0.5*(kron(Id,cdc)+kron(cdc.T,Id))
    return L, dloc


def test_KILLER_round_superop_tp_would_fail_for_no_dissipator_variant():
    # the real round_superop is trace-preserving (tr==1); the no-anticommutator mutant inflates
    # the trace to ~1.35 (a strictly-detectable TP VIOLATION), so test_L1_round_superop_is_cptp
    # has TEETH -- its trace assert is not vacuous.
    E, D = gksl.round_superop(2, ZETA, GAMMA, 0.5, 0.5, 0.35, 0.35, TAU)
    rho = _random_dm(D, seed=1)
    real_tr = np.trace(_apply_super(E, rho, D)).real
    assert abs(real_tr - 1.0) < 1e-9                        # real: trace preserved

    Lb, Db = _build_L_no_dissipator(2, ZETA, GAMMA, 0.5, 0.5, 0.35, 0.35)
    Eb = expm(Lb * TAU)
    buggy_tr = np.trace(_apply_super(Eb, rho, Db)).real
    assert abs(buggy_tr - 1.0) > 1e-2                       # mutant: trace NOT preserved (~1.35)


def _build_sigma_halved_diag(R, tau, zeta, gamma):
    """Sabotage build_sigma: drop the factor of 2 on the diagonal (diag = Gamma_unit, not
    2*Gamma_unit). This reduces diagonal dominance and DESTROYS PSD at the canonical params
    (verified min-eig ~ -0.36 < 0)."""
    diag = 1.0 * cj.gamma_unit_closed(tau, zeta, gamma)     # <-- BUG: missing the 2.0
    S = np.empty((R, R), dtype=float)
    for r in range(R):
        for s in range(R):
            S[r, s] = diag if r == s else cj.sigma_offdiag_closed(abs(r - s), tau, zeta, gamma)
    return S


def test_KILLER_build_sigma_psd_would_fail_for_halved_diag_variant():
    # the real covariance is PSD (min eig > 0); the halved-diagonal mutant has a strictly
    # NEGATIVE eigenvalue at the canonical params, so test_L1_build_sigma_is_symmetric_psd_toeplitz
    # has TEETH -- the eigvals>=0 assert is discriminating, not vacuous.
    R = 3
    real = cj.build_sigma(R, TAU, ZETA, GAMMA)
    assert np.linalg.eigvalsh(real).min() > 1e-6           # real: PSD
    buggy = _build_sigma_halved_diag(R, TAU, ZETA, GAMMA)
    assert np.linalg.eigvalsh(buggy).min() < -1e-2         # mutant: strictly NOT PSD (~-0.36)


def _field_null_unnormalized_weights(*, zeta, gamma, g0z, g1z, tau, n_gh):
    """Sabotage field_null_dual_P_all: DROP the /sqrt(2pi) Gauss-Hermite weight normalization
    (wn = w, not w/sqrt(2pi)). The 3D product weight then integrates to (2pi)^{3/2} instead of 1,
    so the resulting P_all sum is inflated far above 1 -- breaking norm==1. Verbatim structure of
    the real function EXCEPT the one weight line."""
    from numpy.polynomial.hermite_e import hermegauss

    from error_coupling_simulator.quantum_bath.carrier import (
        _extract_x_full,
        _extract_z_full,
        _initial_rho_dual,
        dual_extract,
    )
    from error_coupling_simulator.quantum_bath.gksl import I2, SZ2
    from error_coupling_simulator.quantum_bath.observables import M_ALPHABET

    R = 3
    Sigma = cj.build_sigma(R, tau, zeta, gamma)
    Lchol = np.linalg.cholesky(Sigma)
    x, w = hermegauss(n_gh)
    wn = w                                        # <-- BUG: missing / sqrt(2*pi)

    Sz_data = g0z * np.kron(SZ2, I2) + g1z * np.kron(I2, SZ2)
    Sz_full = np.kron(Sz_data, np.eye(4, dtype=complex))
    sz_diag = np.diag(Sz_full).real
    UX, UZ = _extract_x_full(1), _extract_z_full(1)
    rho0 = _initial_rho_dual(1)
    P_all = {k: 0.0 for k in [(m1, m2, m3) for m1 in M_ALPHABET for m2 in M_ALPHABET
                              for m3 in M_ALPHABET]}

    def rot(phi_r):
        d = np.exp(-1j * sz_diag * phi_r)
        return np.outer(d, d.conj())

    for i in range(n_gh):
        for j in range(n_gh):
            for k in range(n_gh):
                z = np.array([x[i], x[j], x[k]], dtype=float)
                phi = Lchol @ z
                weight = wn[i] * wn[j] * wn[k]
                masks = [rot(phi[r]) for r in range(R)]

                def idle_r(rho, r):
                    return masks[r] * rho

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
    return P_all


def test_KILLER_field_null_norm_would_fail_for_unnormalized_weights_variant():
    # the real field null normalizes to 1 (proper Gaussian expectation); the missing-/sqrt(2pi)
    # mutant sums to ~(2pi)^{3/2} ~ 15.75, a gross norm VIOLATION -- so the norm==1 assert in
    # test_L1_field_null_is_normalized_and_z_inert / test_L0_field_null_* has TEETH.
    P_real, _ = cj.field_null_dual_P_all(zeta=ZETA, gamma=GAMMA, g0z=0.5, g1z=0.5,
                                         tau=TAU, n_gh=2)
    assert sum(P_real.values()) == pytest.approx(1.0, abs=1e-6)      # real: normalized
    P_bug = _field_null_unnormalized_weights(zeta=ZETA, gamma=GAMMA, g0z=0.5, g1z=0.5,
                                             tau=TAU, n_gh=2)
    assert abs(sum(P_bug.values()) - 1.0) > 1.0                      # mutant: grossly un-normalized
    assert sum(P_bug.values()) == pytest.approx((2.0 * math.pi) ** 1.5, rel=1e-6)


# --- KILLER teeth for the field-DEPENDENT K_X pin (HIGH finding) -------------------------- #
# The vacuous L1 asserts (norm==1, K_Z<1e-6, K_joint>=0) ALL survive dropping the entire
# sigma_z field rotation (idle_r -> identity), scaling the field, or using a wrong covariance.
# The K_X match to the independent recon (and > 1e-6 positivity) is shown DISCRIMINATING against each.
def _field_null_KX(*, zeta, gamma, g0z, g1z, tau, n_gh, drop_field=False,
                   field_scale=1.0, cov=None):
    """crow_joynt field null with a sabotage knob, structurally verbatim EXCEPT one edit:
    drop_field -> idle_r becomes identity (the HIGH sabotage); field_scale -> sz_diag*scale;
    cov -> override build_sigma. Returns (K_X, K_joint, norm)."""
    from numpy.polynomial.hermite_e import hermegauss

    from error_coupling_simulator.quantum_bath.carrier import (
        _extract_x_full,
        _extract_z_full,
        _initial_rho_dual,
        dual_extract,
    )
    from error_coupling_simulator.quantum_bath.gksl import I2, SZ2
    from error_coupling_simulator.quantum_bath.observables import (
        K_stat_binary,
        K_stat_joint,
        M_ALPHABET,
        project_axis,
    )

    R = 3
    Sigma = cj.build_sigma(R, tau, zeta, gamma) if cov is None else cov
    Lchol = np.linalg.cholesky(Sigma)
    x, w = hermegauss(n_gh)
    wn = w / math.sqrt(2.0 * math.pi)
    Sz_data = g0z * np.kron(SZ2, I2) + g1z * np.kron(I2, SZ2)
    sz_diag = np.diag(np.kron(Sz_data, np.eye(4, dtype=complex))).real * field_scale
    if drop_field:
        sz_diag = np.zeros_like(sz_diag)               # <-- HIGH sabotage: no field rotation
    UX, UZ = _extract_x_full(1), _extract_z_full(1)
    rho0 = _initial_rho_dual(1)
    P_all = {k: 0.0 for k in [(m1, m2, m3) for m1 in M_ALPHABET for m2 in M_ALPHABET
                              for m3 in M_ALPHABET]}
    P_skip = {k: 0.0 for k in [(m1, m3) for m1 in M_ALPHABET for m3 in M_ALPHABET]}

    def rot(phi_r):
        d = np.exp(-1j * sz_diag * phi_r)
        return np.outer(d, d.conj())

    for i in range(n_gh):
        for j in range(n_gh):
            for k in range(n_gh):
                phi = Lchol @ np.array([x[i], x[j], x[k]], dtype=float)
                weight = wn[i] * wn[j] * wn[k]
                masks = [rot(phi[r]) for r in range(R)]

                def idle_r(rho, r):
                    return masks[r] * rho

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
                    r_ev = idle_r(idle_r(a1, 1), 2)
                    br_sk = dual_extract(r_ev, 1, UX, UZ)
                    for m3 in M_ALPHABET:
                        P_skip[(m1, m3)] += weight * float(np.trace(br_sk[m3]).real)
    PaX, PsX = project_axis(P_all, 0), project_axis(P_skip, 0)
    return K_stat_binary(PaX, PsX), K_stat_joint(P_all, P_skip), sum(P_all.values())


def test_KILLER_field_null_KX_would_fail_for_dropped_or_wrong_field():
    # REAL: K_X matches the independent recon and is positive (field is ON). kx_real is the
    # module's own n_gh=2 value -- the KILLERs show each sabotage shifts K_X AWAY from it.
    out = cj.field_null_point(zeta=ZETA, gamma=GAMMA, g0z=0.5, g1z=0.5, tau=TAU, n_gh=2)
    kx_real = out["K_X"]
    Pr, Psr = _recon_field_null(ZETA, GAMMA, 0.5, 0.5, TAU, 2)
    assert kx_real == pytest.approx(cj.K_stat_binary(cj.project_axis(Pr, 0),
                                                     cj.project_axis(Psr, 0)), abs=1e-9)
    assert kx_real > 1e-6

    # (1) DROP the whole sigma_z field (idle_r -> identity): the exact HIGH sabotage. norm and
    #     K_Z survive it, but K_X collapses to ~0 -- the recon match (and the >1e-6 gate) FAIL.
    kx, kj, nrm = _field_null_KX(zeta=ZETA, gamma=GAMMA, g0z=0.5, g1z=0.5, tau=TAU, n_gh=2,
                                 drop_field=True)
    assert nrm == pytest.approx(1.0, abs=1e-6)                 # vacuous norm SURVIVES the sabotage
    assert kx < 1e-9                                           # but K_X collapses...
    assert abs(kx - kx_real) > 1e-2                            # ...so the K_X match has TEETH
    assert not (kx > 1e-6)                                     # and the strictly-positive gate fires

    # (2) SCALE the field by 2x (a wrong field strength / build_sigma scaling): K_X shifts
    #     materially away from the real value, so the recon match FAILS.
    kx2, _, _ = _field_null_KX(zeta=ZETA, gamma=GAMMA, g0z=0.5, g1z=0.5, tau=TAU, n_gh=2,
                               field_scale=2.0)
    assert abs(kx2 - kx_real) > 1e-2

    # (3) WRONG covariance: use a DIAGONAL-only Sigma (drop the cross-round sigma_offdiag
    #     correlations). Cross-round phase correlation is what generates the X-marginal K, so
    #     K_X collapses to ~0 -- the match FAILS. This gives build_sigma's off-diagonal teeth too.
    Sig_diag = np.diag(np.diag(cj.build_sigma(3, TAU, ZETA, GAMMA)))
    kx3, _, _ = _field_null_KX(zeta=ZETA, gamma=GAMMA, g0z=0.5, g1z=0.5, tau=TAU, n_gh=2,
                               cov=Sig_diag)
    assert kx3 < 1e-9
    assert abs(kx3 - kx_real) > 1e-2


# --- KILLER teeth for the two EMISSION channels of build_shared_bath_liouvillian (LOW) ---- #
# Dropping the sigma_minus emission OR the mode-loss collapse leaves exp(L*tau) exactly CPTP,
# so the CPTP test cannot see them. These variants pin their PHYSICAL effect and show it fails
# when the channel is dropped.
def _build_L_emission_variant(nmax, zeta, gamma, g0z, g1z, g0m, g1m, *,
                              drop_sigma_minus=False, no_factor2=False):
    """build_shared_bath_liouvillian verbatim EXCEPT: drop_sigma_minus removes the qubit->mode
    JC emission terms; no_factor2 uses c=sqrt(gamma)*b (the sqrt(2*gamma) prefactor typo)."""
    b, bdag, num = gksl.boson_ops(nmax)
    Sz0 = np.kron(gksl.SZ2, gksl.I2); Sz1 = np.kron(gksl.I2, gksl.SZ2)
    Sm0 = np.kron(gksl.SM2, gksl.I2); Sm1 = np.kron(gksl.I2, gksl.SM2)
    Scoup_z = g0z * Sz0 + g1z * Sz1
    Scoup_m = g0m * Sm0 + g1m * Sm1
    H = zeta * np.kron(np.eye(4, dtype=complex), num)
    H = H + np.kron(Scoup_z, b + bdag)
    if not drop_sigma_minus:
        H = H + np.kron(Scoup_m, bdag) + np.kron(Scoup_m.conj().T, b)
    gfac = gamma if no_factor2 else 2.0 * gamma
    c = math.sqrt(gfac) * np.kron(np.eye(4, dtype=complex), b)
    dloc = 4 * nmax
    Id = np.eye(dloc, dtype=complex)
    L = -1j * (np.kron(Id, H) - np.kron(H.T, Id))
    cdc = c.conj().T @ c
    L = L + np.kron(c.conj(), c) - 0.5 * np.kron(Id, cdc) - 0.5 * np.kron(cdc.T, Id)
    return L, dloc


def test_KILLER_emission_pins_would_fail_for_dropped_or_mis_scaled_channels():
    nmax = 2
    # REAL mode-loss decay (all couplings 0): exactly exp(-2*gamma*tau).
    L0, d0 = gksl.build_shared_bath_liouvillian(nmax, ZETA, GAMMA, 0.0, 0.0, 0.0, 0.0)
    rho_m1 = _reduced_dm_data_mode(nmax, 0, 1)
    real_decay = _mode_excited_pop(_apply_super(expm(L0 * TAU), rho_m1, d0), nmax)
    assert real_decay == pytest.approx(math.exp(-2.0 * GAMMA * TAU), abs=1e-9)   # ~0.549

    # (A) no-factor-2 (c = sqrt(gamma)*b): decays as exp(-gamma*tau) ~ 0.741, so the
    #     exp(-2*gamma*tau) pin FAILS -- the sqrt(2*gamma) prefactor has teeth.
    Lv, dv = _build_L_emission_variant(nmax, ZETA, GAMMA, 0.0, 0.0, 0.0, 0.0, no_factor2=True)
    slow_decay = _mode_excited_pop(_apply_super(expm(Lv * TAU), rho_m1, dv), nmax)
    assert slow_decay == pytest.approx(math.exp(-GAMMA * TAU), abs=1e-9)          # ~0.741
    assert abs(slow_decay - math.exp(-2.0 * GAMMA * TAU)) > 1e-2                   # pin FAILS

    # REAL sigma_minus JC transfer (excited d0 -> mode): positive mode gain, d0 loses excitation.
    Lm, dm = gksl.build_shared_bath_liouvillian(nmax, ZETA, 0.01, 0.0, 0.0, 0.4, 0.0)
    rho_q = _reduced_dm_data_mode(nmax, 2, 0)
    outm = _apply_super(expm(Lm * TAU), rho_q, dm)
    assert _mode_excited_pop(outm, nmax) > 0.3
    assert _d0_excited_pop(outm, nmax) < 0.7

    # (B) drop the sigma_minus emission: NO transfer -- mode stays empty and d0 stays fully
    #     excited, so BOTH emission asserts FAIL -- the JC coupling has teeth.
    Lb, db = _build_L_emission_variant(nmax, ZETA, 0.01, 0.0, 0.0, 0.4, 0.0, drop_sigma_minus=True)
    outb = _apply_super(expm(Lb * TAU), rho_q, db)
    assert _mode_excited_pop(outb, nmax) < 1e-9        # no excitation reached the mode
    assert _d0_excited_pop(outb, nmax) == pytest.approx(1.0, abs=1e-9)   # d0 frozen fully excited
    assert not (_mode_excited_pop(outb, nmax) > 0.3)   # the L0 emission gate would fire


# --- KILLER teeth for the Liouvillian SIGN structure (couplings / evolution) -------------- #
# A flipped sign on a coupling coefficient (g1z Sz1, g1m Sm1), on the dephasing H term, or on
# the -1j Hamiltonian-evolution factor keeps exp(L*tau) CPTP, so the CPTP test is blind to it.
# The reference-DM pin in test_L0_round_superop_runs_and_is_finite catches each: here we WRITE
# the four flips and verify each moves the evolved DM well outside the pin tolerance.
def _build_L_sign_variant(nmax, zeta, gamma, g0z, g1z, g0m, g1m, *, flip):
    """build_shared_bath_liouvillian verbatim EXCEPT ONE sign flip named by `flip`:
    'g1z' -> g0z*Sz0 - g1z*Sz1; 'g1m' -> g0m*Sm0 - g1m*Sm1; 'dephase' -> H - kron(Scoup_z,...);
    'evolve' -> L = +1j[...] instead of -1j[...]."""
    b, bdag, num = gksl.boson_ops(nmax)
    Sz0 = np.kron(gksl.SZ2, gksl.I2); Sz1 = np.kron(gksl.I2, gksl.SZ2)
    Sm0 = np.kron(gksl.SM2, gksl.I2); Sm1 = np.kron(gksl.I2, gksl.SM2)
    Scoup_z = (g0z * Sz0 - g1z * Sz1) if flip == "g1z" else (g0z * Sz0 + g1z * Sz1)
    Scoup_m = (g0m * Sm0 - g1m * Sm1) if flip == "g1m" else (g0m * Sm0 + g1m * Sm1)
    H = zeta * np.kron(np.eye(4, dtype=complex), num)
    H = (H - np.kron(Scoup_z, b + bdag)) if flip == "dephase" else (H + np.kron(Scoup_z, b + bdag))
    H = H + np.kron(Scoup_m, bdag) + np.kron(Scoup_m.conj().T, b)
    c = math.sqrt(2.0 * gamma) * np.kron(np.eye(4, dtype=complex), b)
    dloc = 4 * nmax
    Id = np.eye(dloc, dtype=complex)
    sgn = 1j if flip == "evolve" else -1j
    L = sgn * (np.kron(Id, H) - np.kron(H.T, Id))
    cdc = c.conj().T @ c
    L = L + np.kron(c.conj(), c) - 0.5 * np.kron(Id, cdc) - 0.5 * np.kron(cdc.T, Id)
    return L, dloc


def test_KILLER_liouvillian_signs_would_fail_the_reference_pin():
    # the |++> evolved-DM reference pin (test_L0_round_superop_*) matches the module to ~1e-9;
    # each sign flip moves it by ~0.1-0.3, so the < 1e-8 pin has TEETH.
    plus = np.array([1.0, 1.0], dtype=complex) / math.sqrt(2.0)
    psi = np.kron(np.kron(plus, plus), np.array([1.0, 0.0], dtype=complex))
    rho0 = np.outer(psi, psi.conj())
    params = (2, ZETA, GAMMA, 0.5, 0.3, 0.35, 0.25)

    E, D = gksl.round_superop(*params, TAU)
    out_real = _apply_super(E, rho0, D)
    Lref, dref = _ref_shared_bath_liouvillian(*params)
    out_ref = _apply_super(expm(Lref * TAU), rho0, dref)
    assert np.max(np.abs(out_real - out_ref)) < 1e-8            # real: matches independent GT

    for flip in ("g1z", "g1m", "dephase", "evolve"):
        Lb, db = _build_L_sign_variant(*params, flip=flip)
        out_bug = _apply_super(expm(Lb * TAU), rho0, db)
        assert np.max(np.abs(out_bug - out_ref)) > 1e-2         # mutant: fails the reference pin

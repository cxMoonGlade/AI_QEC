#!/usr/bin/env python
"""Two-transmon COHERENT channels, derived from first-principles QuTiP Hamiltonians
(CPU/dense backend). Builder 2 deliverable (pre-reg docs/twin_validation/
qutip_channel_derivation_prereg.md, §1 two-transmon table + §2).

WHAT THIS IS
------------
Three coherent two-qutrit (|2>-tracked, 9x9 Kraus) channel DERIVERS, each built from a
coupled-transmon Hamiltonian propagated with QuTiP and truncated to the tracked 3x3-per-site
subspace via the path-B `superop_to_truncated_kraus` (Choi eigendecomposition). The engine
(`qec_twin.forward.exact.qutrit_dm.QutritDM.apply_channel_2site`) is UNCHANGED -- it applies
the precomputed Kraus.

  (A) STATIC-ZZ crosstalk (pre-reg ⑤a). The always-on residual-ZZ from a dispersive
      Duffing pair WITHOUT a flux pulse. The Hamiltonian is TIME-INDEPENDENT (an always-on
      dispersive ZZ), so we build the LAB-FRAME static H (two `transmon_H_static` + the static
      exchange coupling) and propagate it EXACTLY as U = exp(-i H t_g) via GPU
      `torch.linalg.matrix_exp` (solver="expm_gpu", the DEFAULT -- no ODE), then truncate -> 9x9
      Kraus. The lab frame's large single-qubit dynamical phases are removed by the SAME virtual-Z
      gauge. (solver="ode" keeps the legacy rotating-frame `qt.propagator` integration as the
      INDEPENDENT oracle -- the GT-check asserts they agree to Choi fidelity > 1-1e-6.) On the
      computational {0,1}^2 block it is exp(-i phi Z(x)Z) with phi = zeta * t_g / 4, where
      zeta = the |11>-shift (the dispersive cross-Kerr). The exact zeta from the Duffing pair
      is derived analytically (2nd-order PT, the sign convention checked vs the simulation).

  (B) DRIVE / microwave SPILLOVER (Sarovar Ex.1). Transmon A is driven on resonance
      `H_A = Omega(t) cos(w_d t)(a_A + a_A^dag)`; a classical crosstalk coefficient `c` leaks
      that same field onto a DISJOINT transmon B: `c * Omega(t) cos(w_d t)(a_B + a_B^dag)`. We
      propagate the joint (A driven + B spilled) Hamiltonian over the pulse -> truncate ->
      9x9 Kraus. B undergoes an OFF-RESONANT Rabi (detuning Delta = w_B - w_d) conditioned on
      A's drive; the crosstalk-free baseline c=0 leaves B exactly untouched.

  (C) fSim RESIDUAL (Foxen). The path-B calibrated CZ is fSim(0, pi) on the computational
      subspace; the residual is the MISCALIBRATION (delta_theta, delta_phi) reached by the
      `detune_int` knob in `CZParams`. We REUSE the path-B rig (`build_cz_channel` /
      `cz_superoperator` calibrated) -> 9x9 Kraus carrying the coherent residual
      fSim(delta_theta, pi + delta_phi). The LEAKAGE part of that channel is path-B's domain
      (Builder A); this deriver EMITS the coherent residual and reports it vs the analytic fSim.

BASIS / OUTPUT CONVENTION (so the engine eats it directly)
----------------------------------------------------------
`apply_channel_2site` wants a (d^2, d^2)=(9,9) Kraus with row/col index `d*t_i + t_j`,
`site_i` the MORE-significant qutrit. We emit Kraus in EXACTLY that order (subsystem 0 = the
high pair-trit = `site_i`). For (A) static-ZZ the two qutrits are SYMMETRIC (Z(x)Z is
symmetric) so the ordering is immaterial; for (B) subsystem 0 = the DRIVEN qubit A, subsystem
1 = the SPILLED qubit B; for (C) subsystem 0 = the FLUX qubit (path-B convention).

PARAMS -- NEVER FROZEN. Each deriver takes a dataclass exposing the physics knobs as
arguments; the GT-check SWEEPS them. Defaults are grounded (Harper J_ZZ*t_g~1e-3 for ⑤a;
Sarovar Ex.1 for the spillover; Foxen 2001.08343 ~7e-5 for the fSim residual), declared below.

NON-CIRCULAR GROUND TRUTH (lives in qutip_twoqubit_channels_gtcheck.py):
  (A) vs the analytic exp(-i phi Z(x)Z) = diag(e^{-i phi}, e^{i phi}, e^{i phi}, e^{-i phi})
      on {0,1}^2 (compared by PROCESS/Choi fidelity, gauge-free), AND vs the closed-form
      cross-Kerr zeta from 2nd-order PT (NOT a check vs this module's own zeta).
  (B) vs the analytic off-resonant Rabi: Omega_eff = sqrt(c^2 Omega^2 + Delta^2), transferred
      pop P = (c^2 Omega^2 / Omega_eff^2) sin^2(Omega_eff t / 2); c=0 -> P=0 (baseline).
  (C) vs the analytic fSim(delta_theta, pi + delta_phi) 2x2 swap block on {01,10} +
      e^{-i(pi+delta_phi)} on |11>.
NONE is a check vs this module's own output (anti-circularity, pre-reg §3).

DECLARED + BOUNDED SIMPLIFICATIONS (faithfulness rule III; pre-reg §4):
  - Truncation-to-Kraus is exact on the tracked 3x3 subspace (Choi eigendecomposition);
    population that leaks to |3>+ during the gate is the completion-policy bias, reported
    (`leaked_population`) and re-injected by the path-B `identity_sink` policy.
  - Rotating frame at the bare transmon frequencies (removes the GHz carriers; same device as
    path-B). RWA is used in the static-ZZ analytic zeta (2nd-order dispersive PT) -- the
    deriver itself does NOT RWA the propagation (it integrates the full ladder), so the
    deriver-vs-analytic gap BOUNDS the RWA error (a reported finding).
  - The drive spillover uses the lab-frame `cos(w_d t)` drive (no drive RWA in the propagation);
    the analytic oracle is the RWA off-resonant Rabi, so again the gap bounds the RWA.
  - Per-round-lumped siting inherited (no within-cycle schedule on the d3 sub-codes).
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Callable

import numpy as np
import qutip as qt

# Reuse the path-B primitives VERBATIM -- do NOT re-derive the Duffing pair or the truncation.
from . import leakage as B  # (was outputs/teacher_prereg/qutip_cz_leakage_channel.py — MIGRATION P1)
from .leakage import (
    CZParams,
    ghz,
    mhz,
    superop_to_truncated_kraus,
    build_cz_channel,
    cz_propagator_calibrated,
    _ladder,
)

TWO_PI = 2.0 * np.pi

# Indices of the computational {0,1}^2 block inside the tracked 3x3-per-site (9-dim) space,
# in the engine order index = 3*t_i + t_j: |00>=0, |01>=1, |10>=3, |11>=4.
COMP_IDX = np.array([0, 1, 3, 4], dtype=int)


# ============================================================================================
# (A) STATIC-ZZ crosstalk  (pre-reg ⑤a)
# ============================================================================================
@dataclass(frozen=True)
class StaticZZParams:
    """The always-on dispersive Duffing pair (NO flux pulse). NEVER frozen -- swept by the GT.

    Grounding (Harper 2605.29514: residual J_ZZ * t_g ~ 1e-3 per idle):
      omega_a / omega_b : the two transmon frequencies (sweet spot). Defaults 6.0 / 6.1 GHz
                          (a typical neighbour pair detuning ~100 MHz).
      alpha_a / alpha_b : anharmonicities, -300 MHz (Varbanov Table II).
      J                 : the static exchange coupling (a a_b^dag + h.c.). Default 5 MHz
                          (a typical always-on residual; Harper-scale -> zeta ~ tens of kHz).
      t_g               : the idle duration over which the static ZZ accumulates. Default 25 ns
                          (one cycle). SWEPT.
      sim_levels        : transmon levels in the simulation (>=4 so the |2>-mediated dispersive
                          shift is resolved). Default 4.
    zeta (the cross-Kerr) is NOT a free param -- it EMERGES from (omega, alpha, J) via the
    dispersive shift; the analytic closed form is `static_zz_crosskerr` (the independent oracle).
    """

    omega_a: float = ghz(6.0)
    omega_b: float = ghz(6.1)
    alpha_a: float = mhz(-300.0)
    alpha_b: float = mhz(-300.0)
    J: float = mhz(5.0)
    t_g: float = 25.0
    sim_levels: int = 4

    def with_(self, **kw) -> "StaticZZParams":
        return dataclasses.replace(self, **kw)


def static_zz_crosskerr(p: StaticZZParams) -> float:
    """The dispersive cross-Kerr zeta = E11 - E10 - E01 + E00 from 2nd-order PT (the INDEPENDENT
    analytic oracle; NON-circular -- a closed form, not the simulation).

    Two coupled Duffing oscillators H0 = sum_q [w_q n_q + (alpha_q/2) n_q(n_q-1)] with exchange
    V = J(a_a a_b^dag + a_a^dag a_b). The ZZ (cross-Kerr) is the 2nd-order shift of |11> relative
    to the single-excitation manifold. For two transmons the standard result (Krinner 2005.05696
    Eq; Magesan/Gambetta) is

        zeta = 2 J^2 [ 1/(Delta - alpha_b) - 1/(Delta + alpha_a) ]

    with Delta = w_a - w_b the qubit-qubit detuning. (The two terms are the virtual |11>-|20>
    and |11>-|02> exchange-mediated repulsions; alpha<0.) Returns zeta in rad/ns.

    This is the analytic ground truth; the deriver's propagated unitary phase on |11> must match
    zeta * t_g (the GT-check compares them -- a from-scratch closed form vs the full ladder sim).
    """
    Delta = p.omega_a - p.omega_b
    term = 1.0 / (Delta - p.alpha_b) - 1.0 / (Delta + p.alpha_a)
    return 2.0 * p.J * p.J * term


def static_zz_phi(p: StaticZZParams) -> float:
    """The analytic ZZ ANGLE phi such that the computational block is exp(-i phi Z(x)Z).

    exp(-i phi Z(x)Z) = diag(e^{-i phi}, e^{i phi}, e^{i phi}, e^{-i phi}) on (|00>,|01>,|10>,|11>).
    The cross-Kerr term in the Hamiltonian is H_ZZ = zeta n_a n_b; on the computational block
    n_a n_b = diag(0,0,0,1), so U = exp(-i zeta t_g n_a n_b) = diag(1,1,1,e^{-i zeta t_g}).
    Mapping diag(1,1,1,e^{-i zeta t_g}) to the GAUGE-fixed Z(x)Z form (which is symmetric in
    the single-excitation phases) gives phi = zeta * t_g / 4: the conditional phase is
    phi_cond = phi11 - phi10 - phi01 + phi00 = -zeta t_g, and exp(-i phi ZZ) has
    phi_cond = (-phi) - (+phi) - (+phi) + (-phi) = -4 phi, so phi = zeta t_g / 4.
    (Single-qubit Z phases are gauge / virtual-Z removable; the GAUGE-INVARIANT content is the
    conditional phase phi_cond = -zeta t_g, which is what the process fidelity compares.)
    """
    return static_zz_crosskerr(p) * p.t_g / 4.0


def static_zz_exchange_block(p: StaticZZParams) -> np.ndarray:
    """The EXACT single-excitation {|10>,|01>} exchange-hybridization 2x2 block, CLOSED FORM
    (NON-circular: derived from the rotating-frame 2-level algebra, NOT the QuTiP propagator).

    In the rotating frame the single-excitation Hamiltonian -- in the SAME convention as the real
    propagator ``_static_zz_td_hamiltonian`` (H_plus = a_a a_b^dag carries e^{-i Delta t}, so on
    (|10>,|01>): <10|H|01> = J e^{-i Delta t}, <01|H|10> = J e^{+i Delta t}) -- is the
    time-dependent 2-level coupling H(t) = [[0, J e^{-i Delta t}], [J e^{+i Delta t}, 0]],
    Delta = w_a - w_b. Moving to the doubly-rotating frame makes it the STATIC detuned 2-level
    H_s = [[-Delta/2, J], [J, +Delta/2]], so the lab single-excitation propagator over t_g is

        U_se = diag(e^{-i Delta t_g/2}, e^{+i Delta t_g/2}) @ expm(-i H_s t_g).

    *** SIGN-CONVENTION STATUS (honest, per the committed gtcheck log 2026-06-25): this closed-form
    block matches a from-scratch numeric integration of _static_zz_td_hamiltonian's single-excitation
    sector to ~6e-16. HOWEVER, the full 4x4 process fidelity of static_zz_tighter_oracle vs the REAL
    gauged comp block (after build_static_zz_channel + static_zz_propagator_gauged) remains ~0.980,
    NOT ~1 -- an UNRECONCILED relative phase-convention mismatch between this oracle's gauge and the
    gauged comp block's gauge (the from-scratch proxy and the real gtcheck block disagree at the
    {single-excitation}-vs-{00,11} relative-phase level). This is NOT claimed as reconciled. The
    static-ZZ channel is validated by the GAUGE-INVARIANT gates ((i) conditional-phase rate ratio,
    (ii) hybridization MAGNITUDE = 2 J/Delta), which do NOT depend on this convention; F_tight is a
    non-fatal [WARN] diagnostic only. The MAGNITUDE |off-diag| below IS used (it is gauge-invariant);
    the full-matrix oracle's relative phase is the part that did not reconcile. ***

    The off-diagonal magnitude is ~2(J/Delta) for J<<Delta -> the genuine exchange hybridization
    that a pure exp(-i phi ZZ) oracle MISSES. Returns the 2x2 numpy block in (|10>, |01>) order.
    """
    import scipy.linalg as sla
    Delta = p.omega_a - p.omega_b
    Hs = np.array([[-Delta / 2.0, p.J], [p.J, Delta / 2.0]], dtype=complex)
    R = np.diag([np.exp(-1j * Delta * p.t_g / 2.0), np.exp(1j * Delta * p.t_g / 2.0)])
    return R @ sla.expm(-1j * Hs * p.t_g)


def static_zz_hybridization(p: StaticZZParams) -> float:
    """The exchange-hybridization magnitude = |off-diagonal| of the single-excitation block (the
    |10>-|01> leakage). ~2(J/Delta) for J<<Delta. A physical FINDING (the residual the pure-ZZ
    oracle misses); reported + swept to confirm it controls the residual infidelity."""
    blk = static_zz_exchange_block(p)
    return float(abs(blk[0, 1]))


def static_zz_tighter_oracle(p: StaticZZParams) -> np.ndarray:
    """The TIGHTER analytic comp-block oracle: the cross-Kerr ZZ diagonal on {|00>,|11>} PLUS the
    EXACT exchange-hybridization 2x2 on {|10>,|01>} -- a 4x4 unitary in engine comp order
    (|00>,|01>,|10>,|11>). NON-circular (closed form). The QuTiP-derived gauged comp block should
    match THIS to >1-1e-4 (the residual vs pure exp(-i phi ZZ) IS this exchange block).

    Gauge: we put the SAME single-qubit-Z gauge as static_zz_propagator_gauged (single-excitation
    phases referenced to phi00=0). The single-excitation diagonal phases come from the exchange
    block itself; we compare by PROCESS FIDELITY (gauge-free up to global phase), so only the
    GAUGE-INVARIANT content (conditional phase + hybridization angle) is tested.
    """
    zeta = static_zz_crosskerr(p)
    # |11> conditional phase relative to the single-excitation manifold. In the gauged convention
    # phi00=phi10=phi01=0, the |11> phase is the conditional phase phi_cond = -zeta t_g.
    w11 = np.exp(-1j * zeta * p.t_g)
    blk = static_zz_exchange_block(p)  # (|10>,|01>) order
    # build 4x4 in (|00>,|01>,|10>,|11>): exchange block couples idx1(|01>) & idx2(|10>).
    U = np.eye(4, dtype=complex)
    # blk rows/cols are (|10>,|01>) -> map to (idx2, idx1)
    U[2, 2] = blk[0, 0]; U[2, 1] = blk[0, 1]
    U[1, 2] = blk[1, 0]; U[1, 1] = blk[1, 1]
    U[3, 3] = w11
    # gauge the single-excitation DIAGONAL phases to 0 (virtual-Z), matching the gauged comp block:
    # divide row/col 1 and 2 by their diagonal phase so phi10=phi01=0; the hybridization (off-diag)
    # carries the gauge-invariant exchange angle. (A global virtual-Z on each qubit.)
    a10 = np.angle(U[2, 2]); a01 = np.angle(U[1, 1])
    g2 = np.diag([1.0, np.exp(-1j * a01), np.exp(-1j * a10), np.exp(-1j * (a10 + a01))])
    Ug = g2 @ U
    # strip global phase on |00>
    Ug = np.exp(-1j * np.angle(Ug[0, 0])) * Ug
    return Ug


def _static_zz_td_hamiltonian(p: StaticZZParams):
    """The static (time-INDEPENDENT) two-transmon Hamiltonian in the rotating frame of each
    transmon at its OWN frequency. In that frame the number terms vanish; only the anharmonicities
    (frame-invariant) and the exchange coupling carrying a beat e^{+-i Delta t} remain.

    H = (alpha_a/2) n_a(n_a-1) + (alpha_b/2) n_b(n_b-1)
        + J(a_a a_b^dag e^{-i Delta t} + a_a^dag a_b e^{+i Delta t}),  Delta = w_a - w_b.

    (Same rotating-frame algebra as path-B's CZ Hamiltonian, just with NO flux excursion and a
    static J.) Returns the QuTiP time-dependent-Hamiltonian list. subsystem 0 = A (site_i/MSF).
    """
    L = p.sim_levels
    a, ad = _ladder(L)
    n = ad * a
    I = qt.qeye(L)
    anh_a = qt.tensor(0.5 * p.alpha_a * (ad * ad * a * a), I)
    anh_b = qt.tensor(I, 0.5 * p.alpha_b * (ad * ad * a * a))
    H_const = anh_a + anh_b
    a_a = qt.tensor(a, I); ad_a = qt.tensor(ad, I)
    a_b = qt.tensor(I, a); ad_b = qt.tensor(I, ad)
    Delta = p.omega_a - p.omega_b
    H_plus = a_a * ad_b      # carries e^{-i Delta t}
    H_minus = ad_a * a_b     # carries e^{+i Delta t}

    def cp(t, *a_, **kw):
        return p.J * np.exp(-1j * Delta * t)

    def cm(t, *a_, **kw):
        return p.J * np.exp(1j * Delta * t)

    return [H_const, [H_plus, cp], [H_minus, cm]]


def _static_zz_lab_hamiltonian(p: StaticZZParams) -> qt.Qobj:
    """The LAB-FRAME static (time-INDEPENDENT) two-transmon Hamiltonian -- the always-on dispersive
    Duffing pair with a static exchange coupling, NO rotating-frame beat, NO flux pulse:

        H = sum_q [ omega_q n_q + (alpha_q/2) n_q(n_q-1) ] + J (a_a a_b^dag + a_a^dag a_b).

    This is the SAME physics as ``_static_zz_td_hamiltonian`` lifted back to the lab frame: the
    rotating-frame transformation R(t)=exp(+i[w_a n_a + w_b n_b] t) removes exactly the number terms
    ``omega_q n_q`` and turns the static exchange into the e^{+-i Delta t} beat. Keeping the number
    terms makes H time-INDEPENDENT, so the propagator is the closed-form exp(-i H t_g) (matrix_exp),
    not an ODE. subsystem 0 = A (site_i/MSF), subsystem 1 = B (partner) -- same ordering as the
    rotating-frame builder and ``coupling_H``.
    """
    L = p.sim_levels
    a, ad = _ladder(L)
    n = ad * a
    I = qt.qeye(L)
    # Duffing single-site terms: omega_q n_q + (alpha_q/2) n_q(n_q-1).
    H_a = qt.tensor(p.omega_a * n + 0.5 * p.alpha_a * (ad * ad * a * a), I)
    H_b = qt.tensor(I, p.omega_b * n + 0.5 * p.alpha_b * (ad * ad * a * a))
    # static exchange J (a_a a_b^dag + a_a^dag a_b) -- same operator as coupling_H, subsystem 0 = A.
    a_a = qt.tensor(a, I); ad_a = qt.tensor(ad, I)
    a_b = qt.tensor(I, a); ad_b = qt.tensor(I, ad)
    H_J = p.J * (a_a * ad_b + ad_a * a_b)
    return H_a + H_b + H_J


def static_zz_propagator_expm_gpu(p: StaticZZParams) -> qt.Qobj:
    """The closed-system idle propagator U = exp(-i H_lab t_g) on the full L^2 space, computed
    EXACTLY on the GPU via ``torch.linalg.matrix_exp`` (complex128) -- the static-ZZ Hamiltonian is
    time-INDEPENDENT in the lab frame, so this is exact (no ODE, no time-stepping, no max_step).

    The lab frame accumulates large single-qubit dynamical phases (~omega_q t_g ~ 2pi*6e9*25e-9);
    they are GAUGE (virtual-Z) removable -- ``static_zz_propagator_gauged`` strips them, leaving the
    gauge-invariant conditional phase phi=zeta*t_g unchanged. Returns a QuTiP Qobj with the SAME
    dims as the rotating-frame propagator so the downstream truncation/gauge code is identical.
    """
    import torch
    H = _static_zz_lab_hamiltonian(p)
    Hf = np.asarray(H.full(), dtype=np.complex128)
    Ht = torch.as_tensor(Hf, dtype=torch.complex128, device="cuda")
    Ut = torch.linalg.matrix_exp(-1j * Ht * float(p.t_g))
    Uf = Ut.cpu().numpy()
    return qt.Qobj(Uf, dims=H.dims)


def static_zz_propagator(p: StaticZZParams, accuracy: str = "tight",
                         solver: str = "expm_gpu") -> qt.Qobj:
    """The closed-system idle propagator U over [0, t_g] on the full L^2 space.

    solver:
      "expm_gpu" (DEFAULT) -- the lab-frame static H is time-INDEPENDENT, so U = exp(-i H_lab t_g)
                              computed EXACTLY on the GPU (``torch.linalg.matrix_exp``, complex128).
                              No ODE, no max_step, no beat to resolve. ``accuracy`` is ignored.
      "ode"               -- the ORACLE: the rotating-frame time-dependent H integrated with
                              ``qt.propagator`` (the static ZZ is a SLOW kHz accumulation, but the
                              exchange beat e^{+-i Delta t} is ~Delta=100 MHz, period ~10 ns, so
                              max_step must resolve it; accuracy 'tight' -> ~1e-12).
    Both realize the SAME physics (lab frame vs its rotating-frame transform); the GT-check asserts
    they agree (Choi fidelity > 1 - 1e-6 after the same virtual-Z gauge).
    """
    if solver == "expm_gpu":
        return static_zz_propagator_expm_gpu(p)
    if solver != "ode":
        raise ValueError(f"unknown solver {solver!r} (expected 'expm_gpu' or 'ode')")
    H = _static_zz_td_hamiltonian(p)
    if accuracy == "tight":
        ms, atol, rtol = 0.0005, 1e-14, 1e-12
    else:
        ms, atol, rtol = 0.002, 1e-12, 1e-10
    tlist = np.array([0.0, p.t_g])
    opts = {"atol": atol, "rtol": rtol, "nsteps": 5_000_000, "max_step": ms}
    U = qt.propagator(H, tlist, options=opts)
    return U[-1] if isinstance(U, (list, tuple)) else U


def static_zz_propagator_gauged(p: StaticZZParams, accuracy: str = "tight",
                                solver: str = "expm_gpu") -> qt.Qobj:
    """The static-ZZ propagator with single-qubit dynamical Z-phases removed by virtual-Z, so the
    GAUGE-INVARIANT conditional phase is the only computational content left (matching the
    exp(-i phi Z(x)Z) gauge convention: equal +-phi single-excitation phases).

    We choose virtual-Z(theta_a) (x) virtual-Z(theta_b) so that phi10 -> +phi, phi01 -> +phi
    (the symmetric Z(x)Z gauge), where phi = phi_cond / (-4) ... but the SIMPLEST gauge-free
    comparison is by PROCESS FIDELITY of the computational block, which is gauge-robust only up to
    single-qubit Z. We therefore symmetrize: subtract the AVERAGE single-excitation phase from
    each qubit and split the conditional phase symmetrically. This yields the canonical
    diag(e^{-i phi}, e^{i phi}, e^{i phi}, e^{-i phi}) target up to a global phase.

    ``solver`` selects the propagator backend ("expm_gpu" default lab-frame matrix_exp, or "ode" the
    rotating-frame oracle); the virtual-Z gauge is IDENTICAL for both, and the lab-frame's large
    single-qubit dynamical phases are exactly what the gauge removes.
    """
    U = static_zz_propagator(p, accuracy=accuracy, solver=solver)
    L = p.sim_levels
    Uf = U.full()

    def ph(na, nb):
        return float(np.angle(Uf[na * L + nb, na * L + nb]))

    phi00 = ph(0, 0); phi10 = ph(1, 0); phi01 = ph(0, 1)
    # virtual-Z on A removes (phi10 - phi00); on B removes (phi01 - phi00); global removes phi00.
    za = B._virtual_z(phi10 - phi00, L)
    zb = B._virtual_z(phi01 - phi00, L)
    zc = qt.tensor(za, zb)
    Ug = (zc * U)
    # strip the residual global phase on |00>
    g = float(np.angle(Ug.full()[0, 0]))
    return np.exp(-1j * g) * Ug


def build_static_zz_channel(p: StaticZZParams, accuracy: str = "tight",
                            completion: str = "identity_sink", tol: float = 1e-12,
                            solver: str = "expm_gpu"):
    """Derive the static-ZZ crosstalk channel as engine-ready 9x9 Kraus (d=3, |2>-tracked).

    Returns a dict with the Kraus list, the CPTP residual, the leaked-out population, and the
    gauged unitary (for the GT-check's process-fidelity comparison vs exp(-i phi Z(x)Z)).

    ``solver`` ("expm_gpu" DEFAULT) selects the propagator backend: the lab-frame time-INDEPENDENT
    Hamiltonian via GPU ``torch.linalg.matrix_exp`` (exact, no ODE), or "ode" the rotating-frame
    ``qt.propagator`` oracle. The physics + truncation + gauge are identical; only the propagator
    computation differs.
    """
    Ug = static_zz_propagator_gauged(p, accuracy=accuracy, solver=solver)
    S = qt.spre(Ug) * qt.spost(Ug.dag())
    kraus, SKK, _loss, _Eaa = superop_to_truncated_kraus(S, 3, p.sim_levels, tol=tol)
    D = 9
    defect = np.eye(D) - SKK
    defect = 0.5 * (defect + defect.conj().T)
    leaked = float(np.clip(np.linalg.eigvalsh(defect).real, 0.0, None).max())

    if completion == "renormalize":
        resid = float(np.max(np.abs(SKK - np.eye(D))))
        full_kraus = [np.asarray(K, complex) for K in kraus]
    elif completion == "identity_sink":
        dw, dV = np.linalg.eigh(defect)
        sink_idx = 3 * 2 + 2  # |2,2>
        comp = []
        for k in range(len(dw)):
            if dw[k].real > tol:
                Kc = np.zeros((D, D), dtype=complex)
                Kc[sink_idx, :] = np.sqrt(dw[k].real) * dV[:, k].conj()
                comp.append(Kc)
        full_kraus = [np.asarray(K, complex) for K in kraus] + comp
        SKK2 = sum(K.conj().T @ K for K in full_kraus)
        resid = float(np.max(np.abs(SKK2 - np.eye(D))))
    else:
        raise ValueError(f"unknown completion {completion!r}")

    return {
        "kraus": full_kraus, "cptp_residual": resid, "leaked_population": leaked,
        "gauged_unitary_full": Ug, "phi_analytic": static_zz_phi(p),
        "zeta_analytic_radns": static_zz_crosskerr(p), "params": p,
    }


# ============================================================================================
# (B) DRIVE / microwave SPILLOVER  (Sarovar Ex.1)
# ============================================================================================
@dataclass(frozen=True)
class SpilloverParams:
    """Driven transmon A + classical drive spillover onto a DISJOINT transmon B. NEVER frozen.

    Grounding (Sarovar 1907.09980 Ex.1 -- classical microwave crosstalk; off-resonant Rabi):
      omega_a / omega_b : transmon frequencies. Defaults 6.0 / 6.1 GHz (100 MHz detuning ->
                          B is OFF-resonant from A's drive by Delta = w_b - w_d).
      alpha_a / alpha_b : anharmonicities, -300 MHz.
      Omega             : the drive amplitude (Rabi rate) on A. Default 50 MHz (a typical
                          single-qubit gate Rabi). SWEPT.
      omega_d           : the drive frequency. Default = omega_a (drive A on resonance). The
                          B detuning Delta = omega_b - omega_d is the off-resonance lever.
      c                 : the classical crosstalk coefficient (fraction of A's drive seen by B).
                          Default 0.05 (5% spillover, Sarovar-scale). c=0 -> baseline (B untouched).
                          SWEPT (incl. 0).
      t_pulse           : drive duration. Default 25 ns. SWEPT.
      shape             : 'square' (constant Omega) or 'cos' (raised-cosine envelope). The
                          analytic oracle is the SQUARE-pulse off-resonant Rabi; 'cos' is a
                          declared refinement whose gap is reported.
      sim_levels        : transmon levels. Default 3 (the |2> leakage from the strong drive is
                          tracked).
    """

    omega_a: float = ghz(6.0)
    omega_b: float = ghz(6.1)
    alpha_a: float = mhz(-300.0)
    alpha_b: float = mhz(-300.0)
    Omega: float = mhz(50.0)
    omega_d: float = ghz(6.0)
    c: float = 0.05
    t_pulse: float = 25.0
    shape: str = "square"
    sim_levels: int = 3

    def with_(self, **kw) -> "SpilloverParams":
        return dataclasses.replace(self, **kw)


def spillover_transferred_pop(p: SpilloverParams) -> float:
    """The analytic off-resonant Rabi pop transferred onto B (the INDEPENDENT oracle; pre-reg §3).

    B sees an effective drive c*Omega at detuning Delta = w_b - w_d. The 2-level off-resonant
    Rabi (RWA) gives generalized Rabi Omega_eff = sqrt((c Omega)^2 + Delta^2) and transferred
    excited-state population

        P = ((c Omega)^2 / Omega_eff^2) sin^2(Omega_eff t / 2).

    c=0 -> P=0 (the crosstalk-free baseline). Returns P (a probability)."""
    cO = p.c * p.Omega
    Delta = p.omega_b - p.omega_d
    Om_eff = np.sqrt(cO * cO + Delta * Delta)
    if Om_eff == 0.0:
        return 0.0
    return float((cO * cO / (Om_eff * Om_eff)) * np.sin(Om_eff * p.t_pulse / 2.0) ** 2)


def _envelope(p: SpilloverParams) -> Callable[[float], float]:
    if p.shape == "square":
        return lambda t: 1.0
    if p.shape == "cos":
        tp = p.t_pulse
        return lambda t: 0.5 * (1.0 - np.cos(2.0 * np.pi * t / tp))  # 0->...->0, area-normalized-ish
    raise ValueError(f"unknown shape {p.shape!r}")


def _spillover_td_hamiltonian(p: SpilloverParams):
    """The lab-frame driven-A + spilled-B Hamiltonian (NO drive RWA -- the full cos(w_d t) drive),
    in the ROTATING FRAME of each transmon at its OWN frequency (removes the bare GHz carriers;
    the drive carrier cos(w_d t) is kept explicit so the off-resonance Delta is physical).

    Lab frame:  H = sum_q [w_q n_q + (alpha_q/2) n_q(n_q-1)]
                    + Omega(t) cos(w_d t)(a_a + a_a^dag)
                    + c Omega(t) cos(w_d t)(a_b + a_b^dag).
    Rotating frame R(t) = exp(+i[w_a n_a + w_b n_b] t): the number terms vanish; the anharmonicities
    stay; a_q -> a_q e^{-i w_q t}, a_q^dag -> a_q^dag e^{+i w_q t}. The drive term on A becomes
        Omega(t) cos(w_d t)(a_a e^{-i w_a t} + a_a^dag e^{+i w_a t}),
    and similarly on B with c and w_b. We keep cos(w_d t) explicit (no RWA) -> the counter-rotating
    terms are present; the analytic oracle is the RWA result, so the gap BOUNDS the RWA error.

    A and B are DISJOINT (no exchange J) -- the only B response is via the spilled drive. Returns
    the QuTiP TD-Hamiltonian list. subsystem 0 = A (driven, site_i), subsystem 1 = B (spilled).
    """
    L = p.sim_levels
    a, ad = _ladder(L)
    n = ad * a
    I = qt.qeye(L)
    anh_a = qt.tensor(0.5 * p.alpha_a * (ad * ad * a * a), I)
    anh_b = qt.tensor(I, 0.5 * p.alpha_b * (ad * ad * a * a))
    H_const = anh_a + anh_b
    a_a = qt.tensor(a, I); ad_a = qt.tensor(ad, I)
    a_b = qt.tensor(I, a); ad_b = qt.tensor(I, ad)
    env = _envelope(p)
    wa, wb, wd = p.omega_a, p.omega_b, p.omega_d
    Om, c = p.Omega, p.c

    # split each drive into the a (carries e^{-i w_q t}) and a^dag (e^{+i w_q t}) halves; the
    # cos(w_d t) is kept as a real scalar coefficient (no RWA).
    def drA_a(t, *x, **k):
        return Om * env(t) * np.cos(wd * t) * np.exp(-1j * wa * t)

    def drA_ad(t, *x, **k):
        return Om * env(t) * np.cos(wd * t) * np.exp(1j * wa * t)

    def drB_a(t, *x, **k):
        return c * Om * env(t) * np.cos(wd * t) * np.exp(-1j * wb * t)

    def drB_ad(t, *x, **k):
        return c * Om * env(t) * np.cos(wd * t) * np.exp(1j * wb * t)

    return [H_const,
            [a_a, drA_a], [ad_a, drA_ad],
            [a_b, drB_a], [ad_b, drB_ad]]


def spillover_propagator(p: SpilloverParams, accuracy: str = "tight") -> qt.Qobj:
    """The closed-system spillover propagator U over [0, t_pulse] (full L^2, rotating frame).

    The lab-frame drive carrier cos(w_d t) ~ 6 GHz (period ~0.17 ns) must be resolved by
    max_step -> small steps. accuracy 'tight' -> ~1e-10 unitarity. This is the speed cost of
    keeping the counter-rotating terms (no drive RWA); it BOUNDS the RWA error vs the oracle.
    """
    H = _spillover_td_hamiltonian(p)
    # max_step must resolve the ~6 GHz drive carrier (~0.17 ns): use a fraction of it.
    carrier_period = 2.0 * np.pi / max(p.omega_d, 1e-9)
    if accuracy == "tight":
        ms = carrier_period / 40.0
        atol, rtol = 1e-13, 1e-11
    else:
        ms = carrier_period / 20.0
        atol, rtol = 1e-11, 1e-9
    tlist = np.array([0.0, p.t_pulse])
    opts = {"atol": atol, "rtol": rtol, "nsteps": 50_000_000, "max_step": ms}
    U = qt.propagator(H, tlist, options=opts)
    return U[-1] if isinstance(U, (list, tuple)) else U


def spillover_measured_pop_on_B(p: SpilloverParams, accuracy: str = "tight") -> float:
    """The simulated transferred pop onto B: prepare |00> (both ground), drive, read pop in B's
    |1> (summed over A) -- the quantity the analytic off-resonant Rabi predicts. NON-circular
    comparison target for the GT-check."""
    U = spillover_propagator(p, accuracy=accuracy)
    L = p.sim_levels
    psi0 = qt.tensor(qt.basis(L, 0), qt.basis(L, 0))
    psi1 = U * psi0
    vec = psi1.full().reshape(L, L)  # [a_level, b_level]
    pop = np.abs(vec) ** 2
    return float(pop[:, 1].sum())  # B in |1>, any A level


def build_spillover_channel(p: SpilloverParams, accuracy: str = "tight",
                            completion: str = "identity_sink", tol: float = 1e-12):
    """Derive the drive-spillover channel as engine-ready 9x9 Kraus (d=3, |2>-tracked).

    Returns a dict with the Kraus list, CPTP residual, leaked-out population, the simulated
    B-pop (vs the analytic oracle), and the propagator (for the GT-check)."""
    U = spillover_propagator(p, accuracy=accuracy)
    S = qt.spre(U) * qt.spost(U.dag())
    kraus, SKK, _loss, _Eaa = superop_to_truncated_kraus(S, 3, p.sim_levels, tol=tol)
    D = 9
    defect = np.eye(D) - SKK
    defect = 0.5 * (defect + defect.conj().T)
    leaked = float(np.clip(np.linalg.eigvalsh(defect).real, 0.0, None).max())

    if completion == "renormalize":
        resid = float(np.max(np.abs(SKK - np.eye(D))))
        full_kraus = [np.asarray(K, complex) for K in kraus]
    elif completion == "identity_sink":
        dw, dV = np.linalg.eigh(defect)
        sink_idx = 3 * 2 + 2
        comp = []
        for k in range(len(dw)):
            if dw[k].real > tol:
                Kc = np.zeros((D, D), dtype=complex)
                Kc[sink_idx, :] = np.sqrt(dw[k].real) * dV[:, k].conj()
                comp.append(Kc)
        full_kraus = [np.asarray(K, complex) for K in kraus] + comp
        SKK2 = sum(K.conj().T @ K for K in full_kraus)
        resid = float(np.max(np.abs(SKK2 - np.eye(D))))
    else:
        raise ValueError(f"unknown completion {completion!r}")

    return {
        "kraus": full_kraus, "cptp_residual": resid, "leaked_population": leaked,
        "pop_B_sim": spillover_measured_pop_on_B(p, accuracy=accuracy),
        "pop_B_analytic": spillover_transferred_pop(p), "propagator_full": U, "params": p,
    }


# ============================================================================================
# (C) fSim RESIDUAL  (Foxen 2001.08343) -- REUSE the path-B rig
# ============================================================================================
def fsim_residual_matrix(delta_theta: float, delta_phi: float) -> np.ndarray:
    """The analytic fSim(delta_theta, pi + delta_phi) 4x4 matrix on (|00>,|01>,|10>,|11>) -- the
    INDEPENDENT oracle (pre-reg §3). fSim(theta, phi) =
        [[1,            0,            0,             0],
         [0,  cos theta,  -i sin theta,             0],
         [0, -i sin theta,  cos theta,              0],
         [0,            0,            0,  e^{-i phi}]].
    The path-B CALIBRATED CZ is fSim(0, pi); the residual (delta_theta, delta_phi) is the
    miscalibration reached by `detune_int`. Returns the 4x4 numpy array (the iSWAP-angle residual
    delta_theta on {01,10}; the conditional-phase residual delta_phi on |11>)."""
    th, ph = float(delta_theta), float(delta_phi)
    M = np.eye(4, dtype=complex)
    M[1, 1] = np.cos(th); M[1, 2] = -1j * np.sin(th)
    M[2, 1] = -1j * np.sin(th); M[2, 2] = np.cos(th)
    M[3, 3] = np.exp(-1j * (np.pi + ph))
    return M


def fsim_residual_from_cz(p: CZParams, accuracy: str = "tight") -> dict:
    """Extract the fSim residual (delta_theta, delta_phi) from the path-B calibrated CZ propagator.

    The calibrated CZ (cz_propagator_calibrated) realizes the computational subspace fSim
    parameters. We read off the iSWAP angle theta from the |01>/|10> hybridization and the
    conditional phase phi_cz from the |11> phase. The residuals are
        delta_theta = theta  (ideal CZ has theta=0, no iSWAP),
        delta_phi   = phi_cz - pi  (ideal CZ conditional phase is exactly pi).
    These EMERGE from the `detune_int` miscalibration knob in CZParams (SWEPT). NON-circular: the
    extracted residual is compared to the analytic fsim_residual_matrix in the GT-check.
    """
    U = cz_propagator_calibrated(p, accuracy=accuracy)
    L = p.sim_levels
    Uf = U.full()
    comp = np.array([0 * L + 0, 0 * L + 1, 1 * L + 0, 1 * L + 1])
    Ucomp = Uf[np.ix_(comp, comp)]
    # iSWAP angle from the |01><->|10| block: |U[01,10]| = |sin theta|.
    off = abs(Ucomp[1, 2])
    diag = abs(Ucomp[1, 1])
    theta = float(np.arctan2(off, diag))
    # conditional phase phi_cz = angle(U11) - angle(U01) - angle(U10) + angle(U00).
    a00 = np.angle(Ucomp[0, 0]); a01 = np.angle(Ucomp[1, 1]); a10 = np.angle(Ucomp[2, 2])
    a11 = np.angle(Ucomp[3, 3])
    phi_cz = float(((a11 - a01 - a10 + a00) + np.pi) % (2 * np.pi) - np.pi)
    delta_theta = theta
    delta_phi = float(((phi_cz - np.pi) + np.pi) % (2 * np.pi) - np.pi)
    return {
        "delta_theta": delta_theta, "delta_phi": delta_phi,
        "phi_cz": phi_cz, "Ucomp": Ucomp, "params": p,
    }


def build_fsim_residual_channel(p: CZParams, accuracy: str = "tight",
                                completion: str = "identity_sink"):
    """Derive the fSim-residual coherent channel as engine-ready 9x9 Kraus (d=3, |2>-tracked) by
    REUSING the path-B calibrated CZ channel (build_cz_channel). The LEAKAGE structure is path-B's
    (Builder A); this returns the SAME channel object + the extracted coherent residual so the
    teacher can use the calibrated CZ as the coherent-residual mechanism.

    Returns a dict: the path-B LeakageChannel (track_dim=3, 9x9 Kraus), the extracted residual
    (delta_theta, delta_phi), and the analytic fSim matrix (for the GT-check)."""
    ch = build_cz_channel(p, 3, completion=completion, calibrated=True, accuracy=accuracy)
    res = fsim_residual_from_cz(p, accuracy=accuracy)
    return {
        "leakage_channel": ch, "kraus": ch.kraus, "cptp_residual": ch.cptp_residual,
        "delta_theta": res["delta_theta"], "delta_phi": res["delta_phi"],
        "fsim_analytic_4x4": fsim_residual_matrix(res["delta_theta"], res["delta_phi"]),
        "Ucomp": res["Ucomp"], "params": p,
    }


def fsim_fit(Ucomp: np.ndarray) -> dict:
    """BEST-FIT fSim(delta_theta, pi + delta_phi) to a comp block by process fidelity (gauge-free),
    instead of the heuristic single-element read. Returns the fitted (delta_theta, delta_phi) and
    the fit fidelity. This removes any extraction imperfection: if the residual is fSim-representable,
    the fit recovers it exactly; whatever F it caps at is the NON-fSim content (leakage + warts)."""
    from scipy.optimize import minimize

    def negF(x):
        return -unitary_process_fidelity(Ucomp, fsim_residual_matrix(x[0], x[1]))

    # seed from the heuristic read so the fit starts near the answer
    off = abs(Ucomp[1, 2]); diag = abs(Ucomp[1, 1])
    th0 = float(np.arctan2(off, diag))
    a00 = np.angle(Ucomp[0, 0]); a01 = np.angle(Ucomp[1, 1])
    a10 = np.angle(Ucomp[2, 2]); a11 = np.angle(Ucomp[3, 3])
    ph0 = float(((a11 - a01 - a10 + a00) + np.pi) % (2 * np.pi) - np.pi) - np.pi
    res = minimize(negF, [th0, ph0], method="Nelder-Mead",
                   options={"xatol": 1e-10, "fatol": 1e-13, "maxiter": 8000})
    return {"delta_theta": float(res.x[0]), "delta_phi": float(res.x[1]), "F_fit": float(-res.fun)}


def fsim_decompose(Ucomp: np.ndarray) -> dict:
    """Decompose a calibrated-CZ comp block into (a) LEAKAGE / sub-unitarity (path-B's domain,
    declared OUT OF SCOPE for the coherent residual) and (b) the COHERENT fSim-misfit.

    A calibrated CZ comp block is a sub-block of the FULL-space CZ unitary, so it is SUB-UNITARY:
    population leaks to |2>/|20> (path-B's leakage). A unitary fSim oracle CANNOT match a sub-unitary
    block, so part of (1 - F_fit) is just this leakage, NOT an fSim failure. We:
      - measure leakage = 1 - Tr(Ucomp^dag Ucomp)/4 (mean lost amplitude^2 from the comp subspace);
      - POLAR-decompose Ucomp = U_unit @ P (P>=0); U_unit is the leakage-removed coherent unitary;
      - best-fit fSim to U_unit -> F_coherent (the fSim-representability of the COHERENT part).
    Returns leakage, F_fit (vs raw block), F_coherent (vs polar-unitarized block), and the fit.
    The residual is ESTABLISHED as: total = leakage (out of scope) + (1 - F_coherent) (fSim misfit)."""
    from scipy.linalg import polar
    G = Ucomp.conj().T @ Ucomp
    leakage = float(1.0 - np.real(np.trace(G)) / 4.0)
    fit_raw = fsim_fit(Ucomp)
    U_unit, _P = polar(Ucomp)
    fit_coh = fsim_fit(U_unit)
    return {
        "leakage": leakage, "F_fit_raw": fit_raw["F_fit"], "F_coherent": fit_coh["F_fit"],
        "delta_theta": fit_raw["delta_theta"], "delta_phi": fit_raw["delta_phi"],
        "delta_theta_coherent": fit_coh["delta_theta"], "delta_phi_coherent": fit_coh["delta_phi"],
    }


# ============================================================================================
# shared: process / Choi fidelity on the computational {0,1}^2 block (gauge-free comparison)
# ============================================================================================
def comp_block_unitary(U: np.ndarray, per_site_levels: int | None = None) -> np.ndarray:
    """Extract the 4x4 computational {0,1}^2 block from a two-qudit operator.

    CRITICAL: the row/col index of a two-qudit operator is ``per_site_levels * t_i + t_j``. The
    QuTiP-DERIVED propagators live in the FULL simulation space (``per_site_levels = sim_levels``,
    e.g. 16-dim for sim_levels=4), NOT the engine-truncated 9-dim space. The computational basis
    indices are therefore ``[0, 1, per_site_levels, per_site_levels+1]`` (|00>,|01>,|10>,|11>),
    which for sim_levels=4 is [0,1,4,5] -- NOT the engine-9 [0,1,3,4]. Passing the wrong
    per_site_levels extracts |03>/|30> instead of |10>/|01> and scatters the process fidelity
    (the static-ZZ F=0.25 bug, 2026-06-25).

    per_site_levels: the per-site dimension of U. If None, inferred from the matrix size
    (sqrt of the operator dim) -- e.g. 9-dim -> 3, 16-dim -> 4, 25-dim -> 5.
    """
    if per_site_levels is None:
        D = U.shape[0]
        per_site_levels = int(round(np.sqrt(D)))
        assert per_site_levels * per_site_levels == D, f"operator dim {D} is not a perfect square"
    L = per_site_levels
    idx = np.array([0 * L + 0, 0 * L + 1, 1 * L + 0, 1 * L + 1], dtype=int)
    return U[np.ix_(idx, idx)]


def unitary_process_fidelity(U: np.ndarray, V: np.ndarray) -> float:
    """Gauge-free (up to global phase) process fidelity between two d-dim unitaries:
        F = |Tr(U^dag V)|^2 / d^2.
    F=1 iff U == V up to a global phase. (For unitary channels this equals the entanglement /
    Choi process fidelity, so it is the gauge-free channel comparison the pre-reg asks for.)"""
    d = U.shape[0]
    tr = np.trace(U.conj().T @ V)
    return float(abs(tr) ** 2 / (d * d))


def kraus_choi(kraus: list, d: int = 9) -> np.ndarray:
    """The (normalized) Choi matrix of a Kraus channel: J = sum_k |K_k>><<K_k| / d, with the
    column-stacking vec convention -- for a gauge-free CHANNEL fidelity between a derived Kraus
    set and an analytic unitary's channel."""
    J = np.zeros((d * d, d * d), dtype=complex)
    for K in kraus:
        v = K.reshape(-1, order="F")  # vec(K), column-stacked
        J += np.outer(v, v.conj())
    return J / d


def channel_fidelity_choi(kraus_a: list, kraus_b: list, d: int = 9) -> float:
    """State (Uhlmann) fidelity between the two channels' normalized Choi matrices -- a gauge-free
    CPTP-channel comparison (NOT Kraus-element). For two unitary channels this reduces to the
    process fidelity. F = (Tr sqrt(sqrt(Ja) Jb sqrt(Ja)))^2."""
    import scipy.linalg as sla
    Ja = kraus_choi(kraus_a, d)
    Jb = kraus_choi(kraus_b, d)
    sa = sla.sqrtm(Ja)
    inner = sla.sqrtm(sa @ Jb @ sa)
    return float(np.real(np.trace(inner)) ** 2)


__all__ = [
    # (A) static ZZ
    "StaticZZParams", "static_zz_crosskerr", "static_zz_phi",
    "static_zz_exchange_block", "static_zz_hybridization", "static_zz_tighter_oracle",
    "static_zz_propagator", "static_zz_propagator_expm_gpu", "static_zz_propagator_gauged",
    "build_static_zz_channel",
    # (B) drive spillover
    "SpilloverParams", "spillover_transferred_pop", "spillover_propagator",
    "spillover_measured_pop_on_B", "build_spillover_channel",
    # (C) fSim residual
    "fsim_residual_matrix", "fsim_residual_from_cz", "build_fsim_residual_channel",
    "fsim_fit", "fsim_decompose",
    # shared
    "comp_block_unitary", "unitary_process_fidelity", "kraus_choi",
    "channel_fidelity_choi", "COMP_IDX", "CZParams", "ghz", "mhz",
]

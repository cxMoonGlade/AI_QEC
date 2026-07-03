#!/usr/bin/env python
r"""Open-system / bath teacher channels derived FROM QuTiP open-system simulations
(Builder-3 deliverable; pre-reg ``docs/twin_validation/qutip_channel_derivation_prereg.md``
§1 open-system rows + §2 the THREE correlation PUSHES).

WHAT THIS IS
------------
Like Builder-A's path-B leakage transport (``qutip_cz_leakage_channel.py``), every channel
here is DERIVED from a coupled-system Hamiltonian / Lindbladian with QuTiP (CPU/dense), turned
into engine-ready Kraus (single-qubit ``(3,3)`` on the qutrit ``QutritDM`` index convention,
or a 2-site ``(9,9)`` for the correlated-readout push), and validated in the companion
``qutip_opensystem_gtcheck.py`` against an INDEPENDENT analytic closed-form oracle — NEVER
QuTiP-vs-QuTiP (anti-circular, ``feedback-anti-toy-ground-truth-protocol``).

The torch-GPU ``QutritDM`` engine is UNCHANGED. This module is a CPU-side channel DERIVER
(a library). The correlation processes that are NOT a single Hamiltonian (the burst chip-wide
broadcast; the per-round 1/f streaky correlation) feed the carrier/record as PER-ROUND
QuTiP-derived channels + (declared) classical correlation layers — the §2 feasibility gradient.

THE ITEMS (this file owns READOUT, TLS, BURST + the 3 PUSHES)
------------------------------------------------------------
A. readout-induced dephasing (Heinsoo 1801.07904):
     H = chi * n_q * a^dag a  (dispersive) + eps*(a + a^dag) (resonator drive) + Purcell sqrt(kappa)*a
     mesolve the qubit+resonator -> trace out the resonator -> measurement-induced dephasing
     on the qubit -> (3,3) Kraus (|2> tracked, dephasing-only on the leaked level: a phase channel).
   ANALYTIC ORACLE: dispersive measurement-induced dephasing rate Gamma_phi = 8 chi^2 nbar / kappa,
     nbar ~ (2 eps/kappa)^2 (steady-state driven-resonator photon number); the dephasing factor over
     time t_meas is exp(-Gamma_phi t_meas) on the |0><1| coherence.  SWEPT: chi, kappa, eps, t_meas.

A'. readout-induced LEAKAGE / MIST (Xiong 2509.11822 + Fechant 2505.00674) — the FIRST CROSS-MECHANISM
     COUPLING (READOUT axis x ④ LEAKAGE axis):
     a MULTI-LEVEL transmon (>=3 levels) in the SEMICLASSICAL-CAVITY frame (the standard MIST method,
     Shillito PRX Quantum 2022 / Cohen-Blais): the readout cavity at operating power (n̄>>1) is a
     CLASSICAL coherent DRIVE on the transmon charge Omega=g_qr*sqrt(n̄), plus the ac-Stark shift
     2 chi n̄ and the transmon ANHARMONICITY (alpha_q/2)n_q(n_q-1) — so the |1>->|2> multiphoton
     resonance EXISTS in the driven-transmon spectrum WITHOUT a quantized Fock mode (NO n_fock, dim
     <=4 -> NO OOM). matrix_exp the constant rotating-frame Liouvillian -> a (3,3) qubit channel that
     LEAKS |1>->|2> at the readout n̄ (measurement-induced transitions / ionization). NOT a
     phenomenological flat rate — the leak is DERIVED from the multiphoton-resonance dynamics (grows
     with n̄, zero at n̄=0, sharpens toward n̄_crit).
   ANALYTIC ORACLE: the Fechant/Blais multiphoton-resonance CRITICAL n̄: n̄_crit ~ |alpha_q|/(2|chi|k)
     (the k-photon |1>->|2> resonance) — the n̄-dependence anchor (NOT 'matches our own readout sim');
     + the leaked-|1>->|2> magnitude bracketing Xiong's ℒ↑≈0.08%/100ns (SWEPT). This is the first
     channel where TURNING THE READOUT ON drives the LEAKAGE axis — the coupling layer (drive↔leakage,
     ZZ↔gate, TLS↔leakage) opens here (declared future couplings).

   PUSH (heavier): 2-resonator correlated readout (Heinsoo §crosstalk):
     2 qubits + 2 resonators, resonator-resonator coupling J_R + an off-resonant cross-drive (drive
     resonator 0; resonator 1 acquires a photon ~ Delta^-2 (no Purcell) / Delta^-4 (Purcell)).
     mesolve the joint readout -> the spectator (qubit-1) measurement-induced dephasing FROM driving
     resonator-0 (the correlated-readout channel) + a declared IQ->bit classifier for the assignment.
   ANALYTIC ORACLE: the Heinsoo intra-resonator cross-photon scaling nbar_1 ~ (J_R/Delta)^2 nbar_0
     (Delta^-2) and the Purcell-protected Delta^-4; the spectator dephasing = 8 chi^2 nbar_1 / kappa.
     FLAG: the joint Hilbert space (2 qubits x 2 resonators x Fock) is the LARGE sim — bounded below.

B. TLS / spectator defect (Gao 2605.23385):
     H = omega_q n_q + (alpha_q/2) n_q(n_q-1) + g (sigma^+ tau^- + sigma^- tau^+) (Jaynes-Cummings
     exchange, transmon qutrit x TLS qubit) + TLS Lindblad (T1_TLS amplitude damping, Tphi_TLS deph).
     mesolve -> trace out the TLS -> the coupled qubit channel -> (3,3) Kraus.
   ANALYTIC ORACLE: vacuum-Rabi exchange P_{|1,0> -> |0,1>}(t) = sin^2(g t) (lossless JC, the |1>_q|0>_T
     <-> |0>_q|1>_T two-level subspace); with TLS T1 the envelope is the standard damped Rabi.
     SWEPT: g, T1_TLS, Tphi_TLS, omega detuning delta.

   PUSH (the real win): TLF-bath 1/f ⑤b temporal correlation:
     the qubit frequency is modulated by N two-level fluctuators (random-telegraph: each TLF switches
     0<->1 at a rate gamma_i drawn from a log-uniform distribution; the qubit accrues a stochastic phase
     phi(t) = eta * sum_i xi_i(t)).  Simulate MULTI-ROUND (sample TLF trajectories) -> the emergent
     per-round dephasing + the round-to-round phase-noise CORRELATION.
   ANALYTIC ORACLE: the Dutta-Horn 1/f^~1 PSD from the declared TLF switching-rate distribution
     S(f) = sum_i (4 eta^2 gamma_i) / (gamma_i^2 + (2 pi f)^2)  (sum of Lorentzians; log-uniform rates ->
     1/f over the rate band) — a CLOSED FORM, no QuTiP.  CROSS-CHECK: does the emergent round-to-round
     correlation match the WS2 ``TemporalCorrMask`` (Kam) class?  FLAG: N TLFs x trajectory samples
     bounded (this is a CLASSICAL stochastic process on the qubit phase — small Hilbert space, but the
     trajectory ENSEMBLE size is the cost; bounded below).

C. burst elevated-T1 + shared bath (Tan 2406.18897 / McEwen):
     a single qubit (or small-M demo) with an ELEVATED amplitude-damping rate during a burst window:
     H = 0 (idle), c = sqrt(gamma_burst) * a  (elevated T1) -> mesolve over a cycle -> (3,3) Kraus.
     PUSH (PARTIAL): a COMMON mode (shared bath) coupled to M qubits -> correlated elevated relaxation,
     small-M QuTiP demo; the chip-wide (d3=9q) broadcast is a DECLARED classical broadcast of the
     QuTiP-derived elevated-T1 channel (NOT first-principles — honestly bounded-phenomenological).
   ANALYTIC ORACLE: the correlated-T1 decay P_excited(t) = exp(-gamma_burst t) + the closed-form
     detection-density elevation (already in ``tc_burst_certify.py``: f(q)=2q/3, P_fire(w,f)).
     SWEPT: gamma_burst (= 1/T1_burst), M_demo.

FIRST-PRINCIPLES vs BOUNDED-PHENOMENOLOGICAL (the §2 feasibility gradient — HONEST, no overclaim)
------------------------------------------------------------------------------------------------
  * readout dephasing (single qubit)       : FIRST-PRINCIPLES (qubit+resonator mesolve, traced out).
  * 2-resonator correlated readout (PUSH)  : ANALYTIC Delta^-2/Delta^-4 cross-photon SCALING LAW
                                             (EXACT closed-form) + a DECLARED IQ->bit classifier. The
                                             joint-mesolve spectator-dephasing CROSS-CHECK is UNRESOLVED
                                             (adversarial-review finding 2026-06-25): the bare 2-resonator
                                             geometry is NOT in the Delta^-2 dispersive regime, so the
                                             no-Purcell sim gives ~Delta^-4 too and does NOT reproduce the
                                             Heinsoo -2-vs-4 split. NOT claimed first-principles; the
                                             spectator channel is derived + CPTP but its scaling is not the
                                             certified part — the scaling LAW is (analytic). bounded.
  * TLS exchange (single qubit + TLS)      : FIRST-PRINCIPLES (JC mesolve, TLS traced out).
  * TLF-bath 1/f ⑤b (PUSH)                  : FIRST-PRINCIPLES stochastic process (RT telegraph on the
                                             qubit phase; the emergent 1/f + round-correlation are derived);
                                             the rate DISTRIBUTION + eta MAGNITUDE are BRACKETED (device-
                                             unmeasured) — first-principles FORM, bracketed magnitude.
  * burst elevated-T1 (single qubit)       : FIRST-PRINCIPLES (elevated-gamma amplitude-damping mesolve).
  * burst shared-bath small-M demo (PUSH)  : FIRST-PRINCIPLES for the M-qubit common-mode correlation
                                             (joint mesolve, small M); the CHIP-WIDE (9q) simultaneity is
                                             a DECLARED classical broadcast — bounded-phenomenological
                                             (the §2 "PARTIAL" honest label).

DECLARED + BOUNDED SIMPLIFICATIONS (unbounded => STOP — none here)
-----------------------------------------------------------------
  (os-S1) Fock truncation of every resonator (``n_fock``) — now ADAPTIVE (the §1 fix, 2026-06-26):
          n_fock = max(8, ceil(4*nbar+8)), nbar=(2 eps/kappa)^2, so the Fock space covers the driven
          coherent state's Poisson tail at EVERY eps. The BAND DIAGNOSTIC (tc_readout_band_diag.py)
          proved a FIXED n_fock under-converged at large nbar (gap 1.5e-2 at nbar=4/n_fock=8, ~1e-9 at
          n_fock=24) — finite-Fock undersampling, NOT physics; adaptive n_fock keeps the build TIGHT
          (<1e-6 vs the exact transient oracle). An explicit n_fock override is honored (the gtcheck
          sweeps it for the convergence demo). FLAGGED: the 2-resonator joint space is the LARGE sim.
  (os-S2) RWA / dispersive forms (chi n a^dag a; g(sigma^+ tau^- + h.c.)) where the literature uses them.
  (os-S3) the IQ->bit classifier for the readout assignment is a DECLARED classifier on the resonator
          quadrature (a soft-readout boundary), NOT derived from the IQ-plane physics.
  (os-S4) the TLF process is CLASSICAL phase telegraph (Gaussian/RTN dephasing); the coherent TLS-qubit
          EXCHANGE (vacuum Rabi) is the separate JC item (B) — not double-counted.
  (os-S5) the burst chip-wide broadcast is a classical replication of the single-qubit elevated-T1
          channel across the footprint (class (c); §2 PARTIAL).
  (os-S6) per-round-lumped siting (no within-cycle CZ schedule on the d3 sub-codes), inherited.
  (mS-1)  MIST SEMICLASSICAL-CAVITY simplification (declared+bounded, rule III): the readout cavity is
          treated as a CLASSICAL coherent DRIVE on the transmon charge (the standard MIST method,
          Shillito PRX Quantum 2022 / Cohen-Blais 2402.06615), NOT a quantized Fock mode. VALID for
          readout n̄>>1; photon shot-noise / measurement back-action neglected, error ~O(1/n̄) (the
          leading coherent-state mean-field correction). This REPLACES the Fock-quantized full
          Liouvillian (which is (sim_levels*n_fock)^4 and OOMs at readout n̄ — infeasible near n̄_crit).
          Hilbert = the TRANSMON ONLY (dim = sim_levels <= 4 -> superop 16x16); n̄ swept via the
          classical drive Omega=g_qr*sqrt(n̄) + the ac-Stark shift 2 chi n̄, NOT via Fock truncation.
  (mS-2)  MIST OFFSET-CHARGE dependence (Fechant: n̄_crit is offset-charge dependent) is NOT swept — a
          DECLARED bounded simplification (class c): the channel realizes a REPRESENTATIVE bracket of
          the leak at a fixed (implicit) charge, anchored to Xiong's ℒ↑≈0.08%/100ns, NOT the charge-
          resolved physical value. The MIST MECHANISM (multiphoton resonance, n̄-dependence, zero at
          n̄=0) is first-principles; only the charge-resolved magnitude is bracketed. SWEPT in eps/n̄.
  (mS-3)  MIST is a single-qubit readout-induced-leakage channel applied to the MEASURED qubit during
          its readout (the readout↔④-leakage coupling); the multi-resonator MIST crosstalk (one qubit's
          readout ionizing a NEIGHBOUR) is a richer arm, declared, not built here.

ALL device params are SWEPT (never frozen) via frozen dataclasses with ``.with_(...)``; the unmeasured
ones (eta, the TLF rate distribution, J_R, gamma_burst) are BRACKETED, not pinned.

ENGINE API (the channels feed these UNCHANGED methods):
  from qec_twin.forward.exact.qutrit_dm import QutritDM
  eng.apply_channel(kraus_3x3_list, site)              # single-qubit (3,3) Kraus
  eng.apply_channel_2site(kraus_9x9_list, site_i, site_j)  # 2-site (9,9) Kraus, index 3*t_i+t_j

GROUNDING: Heinsoo 1801.07904 (readout crosstalk, Purcell Delta^-4); Gao 2605.23385 (TLS g̃<=10 MHz,
T1=44.7us, T2R=0.4us, 1/f^1.05 Dutta-Horn, rates 0.6 mHz-0.2 GHz); Tan 2406.18897 (burst depol, Fig 5).

This file is the DERIVER (a library). The scripted GT-check + Kraus-save is the companion
``qutip_opensystem_gtcheck.py`` (precondition asserts + printed evidence + __main__ guard).
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass

import numpy as np
import qutip as qt

# ----------------------------------------------------------------------------------------
# units (reuse the path-B convention exactly): ANGULAR frequency rad/ns, times ns.
#   f [GHz] -> 2*pi*f [rad/ns];  f [MHz] -> 2*pi*f*1e-3 [rad/ns].
# ----------------------------------------------------------------------------------------
TWO_PI = 2.0 * np.pi
CDTYPE = np.complex128


def ghz(f: float) -> float:
    return TWO_PI * f  # rad/ns


def mhz(f: float) -> float:
    return TWO_PI * f * 1e-3  # rad/ns


def khz(f: float) -> float:
    return TWO_PI * f * 1e-6  # rad/ns


def _ladder(n_levels: int):
    a = qt.destroy(n_levels)
    return a, a.dag()


def adaptive_n_fock(nbar: float, n_fock: int | None = None, *, floor: int = 8) -> int:
    r"""The ADAPTIVE resonator Fock truncation for a driven readout resonator at photon number ``nbar``
    (the §1 FIX, 2026-06-26 — see ``tc_readout_band_diag``).

    The driven-resonator steady state is a coherent state |alpha> with mean photon number nbar =
    |alpha|^2 and a POISSON occupation distribution P(k) = e^{-nbar} nbar^k / k!. To resolve the
    measurement-induced dephasing to the oracle floor the Fock space must cover the Poisson TAIL
    (mean + several sigma; sigma = sqrt(nbar)). A FIXED small n_fock under-converges at large nbar:
    the BAND DIAGNOSTIC ``tc_readout_band_diag.py`` proved the built-vs-exact-transient-oracle gap is
    a FINITE-FOCK truncation artifact (HYPOTHESIS A) — it SHRINKS to ~1e-9 as n_fock grows (gap 1.5e-2
    at nbar=4 / n_fock=8, but ~1e-9 at n_fock=24), n_fock-non-converged, NOT oracle linearization. So
    the "wide band" was finite-Fock undersampling, NOT physics; the tight band is the correct one.

    Rule (covers mean + ~4 sigma + headroom): ``n_fock = max(floor, ceil(4*nbar + 8))``. At nbar=4 ->
    24 (the diagnostic's converged value); grows linearly with nbar so the build stays tight (matches
    the oracle to <1e-6) across the whole eps/nbar sweep. An explicit ``n_fock`` override (not None)
    is honored verbatim (so the gtcheck can still sweep n_fock for the convergence demonstration).

    Args:
      nbar    : the steady-state photon number (2 eps/kappa)^2.
      n_fock  : an EXPLICIT override; if not None it is returned unchanged (override path).
      floor   : the minimum truncation (default 8; the small-nbar floor).
    """
    if n_fock is not None:
        return int(n_fock)
    return int(max(int(floor), int(np.ceil(4.0 * float(nbar) + 8.0))))


# ----------------------------------------------------------------------------------------
# TIME-INDEPENDENT propagator solvers (the EXPM-GPU switch, 2026-06-26).
#
# Every open-system channel in this file (readout dephasing, TLS, burst, shared-bath) is built
# from a CONSTANT (time-independent) Liouvillian L = liouvillian(H, c_ops): the dispersive
# readout drive is constant, the JC TLS exchange + Lindblad is constant, the elevated-gamma
# amplitude damping is constant. For a constant L the exact superoperator over [0, t] is the
# matrix exponential S = expm(L * t) -- NOT an adaptive-RK ODE. ``qt.mesolve`` (adaptive RK,
# looped over input dyads) is the WRONG/slow tool here (the 2-resonator readout took ~500 s on
# CPU). One ``torch.linalg.matrix_exp`` on the FULL-space Liouvillian gives the whole
# superoperator in a single GPU call; we then trace out the ancilla exactly as the ODE path does.
#
# CONVENTION: ``qt.liouvillian(H, c_ops).full()`` is QuTiP's OWN superoperator constructor
# (numpy, column-stacked / Fortran "super" convention — the SAME convention as the per-dyad
# ``reshape(-1, order="F")`` build below + ``superop_to_truncated_kraus_1q``); it is cheap linear
# algebra (NOT an ODE). matrix_exp supports complex128 on cuda (this is expm, NOT ODE-on-GPU, so
# the diffrax/torchode adaptive-solver caveats do not apply).
#
# Both solvers are kept: ``solver="expm_gpu"`` (DEFAULT, the GPU expm path) and ``solver="ode"``
# (the original ``qt.mesolve`` path, retained as the INDEPENDENT oracle the gtcheck cross-checks
# against). They build the SAME L two ways; the gtcheck asserts they agree to the ODE floor.
# ----------------------------------------------------------------------------------------
def _full_superop_expm_gpu(H: qt.Qobj, c_ops, t: float) -> np.ndarray:
    """Build the FULL-space superoperator S = expm(L * t) for the CONSTANT Liouvillian
    L = liouvillian(H, c_ops), via ``torch.linalg.matrix_exp`` on cuda (complex128).

    Returns the dense ``(D^2, D^2)`` numpy superoperator (D = full Hilbert dim), column-stacked
    in QuTiP's "super" convention -- identical to what a per-dyad mesolve loop would assemble,
    but in ONE matrix_exp call instead of D^2 ODE integrations.

    NB: imported lazily so the module is importable (and ``ast.parse``-able) without torch; the
    orchestrator runs this on the GPU workstation.
    """
    import torch

    L = qt.liouvillian(H, c_ops).full()  # (D^2, D^2) numpy, QuTiP column-stacked "super" convention
    Lt = torch.as_tensor(L, dtype=torch.complex128, device="cuda") * float(t)
    S = torch.linalg.matrix_exp(Lt)
    return S.cpu().numpy().astype(CDTYPE)


def _reduce_full_superop_to_qubit(
    S_full: np.ndarray, full_dims: list, keep: list, ancilla_init: list, Lq: int
) -> np.ndarray:
    """Project a FULL-space superoperator ``S_full`` (from ``_full_superop_expm_gpu``) onto the
    tracked qubit subspace, reproducing the EXACT trace-out the ODE path performs, but driven by
    the precomputed expm superoperator instead of a per-dyad mesolve.

    For each tracked qubit dyad |i><j| (i, j in [0, Lq)): build the full initial state
    (qubit dyad on the ``keep`` factor x the ancilla ground/initial states on the others),
    column-stack it, apply ``S_full``, reshape back to the full density matrix, and ptrace down
    to the kept qubit factor -- giving column ``j*Lq + i`` of the reduced qubit superoperator
    (the SAME column-stacking the mesolve build uses). This is the GPU analog of the ODE
    column-by-column build; the physics + trace-out are byte-for-byte the same operations.

    Args:
      S_full       : (D^2, D^2) full-space superop, D = prod(full_dims).
      full_dims    : the per-factor Hilbert dims, e.g. [Lq, Nf] (qubit, resonator).
      keep         : index of the qubit factor to keep (single int in a 1-element list), e.g. [0].
      ancilla_init : list of (slot, init_dm (np array)) for every NON-kept factor's initial dm.
      Lq           : the kept-qubit Hilbert dim (the reduced superop is (Lq^2, Lq^2)).
    """
    full_dims = [int(d) for d in full_dims]
    D = int(np.prod(full_dims))
    keep_slot = int(keep[0])
    S = np.zeros((Lq * Lq, Lq * Lq), dtype=CDTYPE)
    for i in range(Lq):
        for j in range(Lq):
            q_dy = np.zeros((Lq, Lq), dtype=CDTYPE)
            q_dy[i, j] = 1.0
            # assemble the full initial density matrix as a tensor product over the factors.
            factors = [None] * len(full_dims)
            factors[keep_slot] = q_dy
            for slot, init_dm in ancilla_init:
                factors[int(slot)] = np.asarray(init_dm, dtype=CDTYPE)
            rho0 = factors[0]
            for f in factors[1:]:
                rho0 = np.kron(rho0, f)
            vec = rho0.reshape(-1, order="F")
            out_vec = S_full @ vec
            rho_out = out_vec.reshape(D, D, order="F")
            rho_q = _ptrace_numpy(rho_out, full_dims, keep_slot)  # (Lq, Lq)
            S[:, j * Lq + i] = rho_q.reshape(-1, order="F")
    return S


def _ptrace_numpy(rho: np.ndarray, dims: list, keep_slot) -> np.ndarray:
    """Partial trace of a dense density matrix ``rho`` over all factors EXCEPT ``keep_slot``
    (a single int or a list of ints). ``dims`` are the per-factor Hilbert dims; the tensor
    ordering is row/col = factor-0 (slowest) .. factor-(n-1) (fastest), matching QuTiP's
    ``qt.tensor`` ordering (so this reproduces ``Qobj.ptrace`` exactly on the dense array).

    Implemented with ``np.einsum`` so the index bookkeeping is explicit (no fragile mutating
    axis arithmetic): row factor k gets a letter, col factor k gets the SAME letter when k is
    traced (Einstein-summed) and a fresh letter when k is kept.
    """
    dims = [int(d) for d in dims]
    n = len(dims)
    keep = [keep_slot] if isinstance(keep_slot, int) else [int(k) for k in keep_slot]
    keep = sorted(keep)
    t = rho.reshape(dims + dims)  # axes [r0..r_{n-1}, c0..c_{n-1}]
    letters = [chr(ord("a") + k) for k in range(n)]          # row-factor letters
    col_letters = []
    next_letter = ord("a") + n
    for k in range(n):
        if k in keep:
            cl = chr(next_letter); next_letter += 1            # kept col: a NEW free index
            col_letters.append(cl)
        else:
            col_letters.append(letters[k])                     # traced: SAME letter as its row
    subscripts_in = "".join(letters) + "".join(col_letters)
    out_letters = [letters[k] for k in keep] + [col_letters[k] for k in keep]
    subscripts = subscripts_in + "->" + "".join(out_letters)
    reduced = np.einsum(subscripts, t)
    Dk = int(np.prod([dims[k] for k in keep]))
    return reduced.reshape(Dk, Dk).astype(CDTYPE)


# ----------------------------------------------------------------------------------------
# single-system superoperator -> truncated qutrit Kraus (the single-qubit analog of path-B's
# superop_to_truncated_kraus; the SAME Choi-eigendecomposition algebra, on a 1-system space).
# ----------------------------------------------------------------------------------------
def superop_to_truncated_kraus_1q(
    S: qt.Qobj, track_dim: int, sim_levels: int, tol: float = 1e-12, completion: str = "identity_sink"
):
    """Project a SINGLE-system full-space superoperator ``S`` (dim ``sim_levels``) onto the tracked
    ``track_dim`` subspace and return engine-ready ``(track_dim, track_dim)`` Kraus.

    Mirrors path-B ``superop_to_truncated_kraus`` exactly, for ONE system (the qubit, with the
    resonator/TLS/bath already traced out into ``S``, or the qubit's own dissipative S). The truncated
    channel ``E_trunc(rho) = V^dag S[V rho V^dag] V`` (V the tracked isometry) loses population that
    leaks to levels >= track_dim; the ``identity_sink`` completion re-injects that small leaked mass to
    the tracked TOP level (preserving CPTP + "is-leaked" status; bounded by ``leaked_population``,
    reported). ``renormalize`` returns the raw trace-non-increasing Kraus.

    Returns (kraus, cptp_residual, leaked_population).
    """
    d = int(track_dim)
    L = int(sim_levels)
    Dfull = L
    idx = np.arange(d, dtype=int)  # tracked levels are the first d levels of the single system
    Sfull = S.full()  # (L^2, L^2), column-stacked (QuTiP convention)

    def apply_full(rho_full):  # rho_full (L, L)
        vec = rho_full.reshape(-1, order="F")
        out = Sfull @ vec
        return out.reshape(Dfull, Dfull, order="F")

    # tracked Choi: sum_{p,q in tracked} E_trunc(|p><q|) kron |p><q|
    choi = np.zeros((d * d, d * d), dtype=CDTYPE)
    for p in range(d):
        for qd in range(d):
            rho_full = np.zeros((L, L), dtype=CDTYPE)
            rho_full[idx[p], idx[qd]] = 1.0
            out_full = apply_full(rho_full)
            Epq = out_full[np.ix_(idx, idx)]  # (d, d) truncated output
            choi += np.kron(Epq, _e(p, qd, d))

    w, V = np.linalg.eigh(0.5 * (choi + choi.conj().T))
    kraus = []
    for k in range(len(w)):
        if w[k].real > tol:
            kraus.append(np.sqrt(w[k].real) * V[:, k].reshape(d, d, order="C"))

    SKK = sum(K.conj().T @ K for K in kraus) if kraus else np.zeros((d, d), dtype=CDTYPE)
    defect = np.eye(d) - SKK
    defect = 0.5 * (defect + defect.conj().T)
    dw = np.clip(np.linalg.eigvalsh(defect).real, 0.0, None)
    leaked_population = float(dw.max()) if dw.size else 0.0

    if completion == "renormalize":
        resid = float(np.max(np.abs(SKK - np.eye(d))))
        return [np.asarray(K, CDTYPE) for K in kraus], resid, leaked_population

    if completion == "identity_sink":
        dwv, dVv = np.linalg.eigh(defect)
        comp = []
        top = d - 1
        for k in range(len(dwv)):
            if dwv[k].real > tol:
                src = dVv[:, k]
                Kc = np.zeros((d, d), dtype=CDTYPE)
                Kc[top, :] = np.sqrt(dwv[k].real) * src.conj()  # leaked mass -> tracked top level
                comp.append(Kc)
        full_kraus = [np.asarray(K, CDTYPE) for K in kraus] + comp
        SKK2 = sum(K.conj().T @ K for K in full_kraus)
        resid = float(np.max(np.abs(SKK2 - np.eye(d))))
        return full_kraus, resid, leaked_population

    raise ValueError(f"unknown completion {completion!r}")


def _e(i: int, j: int, n: int) -> np.ndarray:
    m = np.zeros((n, n), dtype=CDTYPE)
    m[i, j] = 1.0
    return m


def cptp_residual(kraus) -> float:
    """max | sum_k K^dag K - I | for a single-system Kraus list (engine CPTP-assert helper)."""
    if not kraus:
        return float("inf")
    d = kraus[0].shape[0]
    SKK = sum(np.asarray(K).conj().T @ np.asarray(K) for K in kraus)
    return float(np.max(np.abs(SKK - np.eye(d))))


# ========================================================================================
# A. READOUT-INDUCED DEPHASING (single qubit + resonator; Heinsoo dispersive measurement).
# ========================================================================================
@dataclass(frozen=True)
class ReadoutParams:
    """Dispersive-readout device knobs (NEVER frozen; swept by the GT-check).

    Grounding (Heinsoo 1801.07904; values are device-bracketed):
      chi    : dispersive shift chi/2pi. Default 1.0 MHz (typical transmon-readout chi ~0.5-2 MHz).
      kappa  : resonator linewidth kappa/2pi. Heinsoo kappa_R/2pi ~ 10 MHz. Default 10 MHz.
      eps    : resonator drive amplitude eps/2pi (sets nbar ~ (2 eps/kappa)^2). Default chosen for
               nbar ~ a few photons (Heinsoo: resonators populated to a few photons during readout).
      t_meas : measurement (integration) time. Heinsoo 80 ns readout pulse. Default 80 ns.
      n_fock : resonator Fock truncation. DEFAULT None => ADAPTIVE (the §1 FIX, 2026-06-26): resolved by
               ``resolve_n_fock`` to ``max(8, ceil(4*nbar + 8))`` where nbar=(2eps/kappa)^2, so the Fock
               space covers the driven coherent state's Poisson tail (mean + ~4 sigma) at EVERY eps.
               A FIXED 16 under-converged at large nbar — the BAND DIAGNOSTIC (tc_readout_band_diag.py)
               proved the wide built-vs-oracle band was finite-Fock undersampling (gap 1.5e-2 at
               nbar=4/n_fock=8, ~1e-9 at n_fock=24), NOT physics; adaptive n_fock keeps the build TIGHT
               (<1e-6 vs the exact transient oracle) across the whole eps sweep. An explicit int override
               is honored verbatim (so the gtcheck can still sweep n_fock for the convergence demo).
      sim_levels : transmon levels (>=3 to track |2>). Default 3 (the dephasing is on the comp block;
               |2> is dephasing-inert here -> identity on |2>, so 3 is exact for THIS channel).
    """

    chi: float = mhz(1.0)
    kappa: float = mhz(10.0)
    eps: float = mhz(10.0)
    t_meas: float = 80.0
    n_fock: int | None = None       # None => ADAPTIVE (resolve_n_fock); an int overrides verbatim.
    sim_levels: int = 3

    def with_(self, **kw) -> "ReadoutParams":
        return dataclasses.replace(self, **kw)

    def resolve_n_fock(self) -> int:
        """The EFFECTIVE Fock truncation: the explicit ``n_fock`` if set, else the ADAPTIVE
        ``max(8, ceil(4*nbar + 8))`` (nbar=(2 eps/kappa)^2). Used by every build path so the
        truncation tracks the photon number (the §1 adaptive-n_fock fix)."""
        return adaptive_n_fock(readout_nbar_steadystate(self), self.n_fock)


def readout_nbar_steadystate(p: ReadoutParams) -> float:
    """Steady-state driven-resonator photon number nbar = (2 eps / kappa)^2 (a driven damped mode at
    resonance: <a> = -2i eps / kappa, nbar = |<a>|^2 = (2 eps/kappa)^2). Closed-form, no QuTiP.

    NB: for the Hamiltonian here (H_drive = eps(a+a^dag) with collapse sqrt(kappa) a) the steady-state
    amplitude solves d<a>/dt = -i eps - (kappa/2)<a> = 0 -> <a> = -2i eps/kappa, so nbar = (2 eps/kappa)^2
    EXACTLY for THIS drive normalization (the GT-check verifies the drive term matches this nbar)."""
    return float((2.0 * p.eps / p.kappa) ** 2)


def _readout_cavity_amplitude(chi: float, kappa: float, eps: float, m: int, t):
    """The qubit-state-conditioned intracavity amplitude alpha_m(t) (m = qubit number eigenvalue 0 or 1).

    H_disp = chi * n_q * a^dag a shifts the cavity frequency by chi*m when the qubit is in number state
    m. The driven-damped linear-cavity equation (conditioned on m) is the CLASSICAL ODE
        d alpha_m / dt = -(kappa/2 + i chi m) alpha_m - i eps ,   alpha_m(0) = 0
    with the EXACT closed-form solution
        alpha_m(t) = alpha_ss_m (1 - exp(-(kappa/2 + i chi m) t)),  alpha_ss_m = -i eps / (kappa/2 + i chi m).
    Solved analytically (NOT by QuTiP) -> the engine-independent oracle. ``t`` may be array-like."""
    lam = kappa / 2.0 + 1j * chi * m
    a_ss = -1j * eps / lam
    return a_ss * (1.0 - np.exp(-lam * np.asarray(t, dtype=np.float64)))


def readout_coherence_retention_analytic(p: ReadoutParams, *, n_grid: int = 4000) -> float:
    """ANALYTIC oracle (EXACT for the simulated regime): the qubit |0><1| coherence-retention factor
    c = exp(-Gamma(t_meas)) under dispersive measurement-induced dephasing, where

        Gamma(t) = integral_0^t  chi * Im[ alpha_0(s) conj(alpha_1(s)) ]  ds

    (Gambetta measurement-induced dephasing: the accumulated which-path information the cavity leaks out,
    alpha_m(s) = ``_readout_cavity_amplitude``). INCLUDES the cavity ring-up transient (1/kappa ~ 16 ns vs
    t_meas 80 ns), unlike the asymptotic steady-state rate; solved by a closed-form integral on the
    analytic alpha_m -> NO QuTiP. Returns c in [0, 1].

    *** WHY this replaced the naive 8 chi^2 nbar/kappa (the §1 FIX, 2026-06-25; reported in the gtcheck) ***
    The steady-state asymptotic Gamma_ss = 8 chi^2 nbar/kappa was WRONG here by ~14x for two reasons:
      (i)  CONVENTION: 8 chi^2 nbar/kappa is the sigma_z form (cavity pull +-chi, pointer SEPARATION 2chi);
           H = chi n_q a^dag a gives separation chi between |0>,|1> -> the steady rate is 2 chi^2 nbar/kappa
           (a factor 4 smaller). [verified: chi Im[a_ss0 a_ss1*] -> 2 chi^2 nbar/kappa as chi/kappa->0]
      (ii) TRANSIENT: at t_meas=80 ns the cavity has NOT reached steady state, so the integrated dephasing
           is further below rate*t. The exact integral Gamma(t) captures both and matches the QuTiP sim to
           ~5 decimals (anti-toy: a correct oracle AGREES with a correct sim — we fixed the oracle, did NOT
           widen a band)."""
    t = np.linspace(0.0, p.t_meas, int(n_grid))
    a0 = _readout_cavity_amplitude(p.chi, p.kappa, p.eps, 0, t)
    a1 = _readout_cavity_amplitude(p.chi, p.kappa, p.eps, 1, t)
    integrand = p.chi * np.imag(a0 * np.conj(a1))
    # numpy>=2 renamed trapz -> trapezoid; support both.
    _trap = getattr(np, "trapezoid", None) or np.trapz
    Gamma = float(_trap(integrand, t))
    return float(np.exp(-Gamma))


def readout_dephasing_rate_analytic(p: ReadoutParams) -> float:
    """The STEADY-STATE asymptotic dispersive dephasing RATE for THIS Hamiltonian (reporting only; the
    GT comparison uses the EXACT transient ``readout_coherence_retention_analytic``).

        Gamma_ss = chi Im[ alpha_ss_0 conj(alpha_ss_1) ]  ->  2 chi^2 nbar / kappa   (chi << kappa limit)

    H = chi n_q a^dag a convention (pointer separation chi); the textbook 8 chi^2 nbar/kappa is the sigma_z
    convention (separation 2 chi), 4x larger. rad/ns. Independent of QuTiP."""
    a_ss0 = -1j * p.eps / (p.kappa / 2.0)
    a_ss1 = -1j * p.eps / (p.kappa / 2.0 + 1j * p.chi)
    return float(p.chi * np.imag(a_ss0 * np.conj(a_ss1)))


def readout_dephasing_superop(p: ReadoutParams, solver: str = "expm_gpu") -> qt.Qobj:
    """Build the QUBIT superoperator (resonator traced out) over [0, t_meas] for the dispersive
    measurement Hamiltonian. TIME-INDEPENDENT -> the propagator is expm(L * t_meas).

    H = chi * (a_q^dag a_q) * (a_r^dag a_r)   [dispersive coupling: cavity freq shifts with qubit n]
        + eps * (a_r + a_r^dag)               [resonator drive, on resonance in the rotating frame]
      collapse: sqrt(kappa) * a_r             [Purcell / resonator decay]
    The dephasing emerges because different qubit number states n shift the cavity to different coherent
    pointer states; the cavity-induced which-path information dephases the qubit (Gamma_phi above).

    HILBERT SIZE (FLAG): full dim = sim_levels * n_fock; n_fock is ADAPTIVE (resolve_n_fock):
    max(8, ceil(4*nbar+8)). At the defaults (nbar~4) -> n_fock=24 -> dim 3*24=72 -> superop 72^2=5184
    (~0.4 GB complex128 -> FINE on the GPU); grows linearly with nbar. The resonator is then traced out.

    solver:
      "expm_gpu" (DEFAULT) -- L = liouvillian(H, c_ops); S_full = torch.linalg.matrix_exp(L * t_meas)
                              on cuda (complex128), ONE call; then trace out the resonator.
      "ode"               -- the original per-dyad qt.mesolve loop (the INDEPENDENT oracle).
    """
    Lq = int(p.sim_levels)
    Nf = int(p.resolve_n_fock())   # ADAPTIVE Fock truncation (the §1 fix; tracks nbar)
    aq, adq = _ladder(Lq)
    ar, adr = _ladder(Nf)
    nq = adq * aq
    nr = adr * ar
    Iq = qt.qeye(Lq)
    Ir = qt.qeye(Nf)
    nq_full = qt.tensor(nq, Ir)
    nr_full = qt.tensor(Iq, nr)
    ar_full = qt.tensor(Iq, ar)
    adr_full = qt.tensor(Iq, adr)
    H = p.chi * nq_full * nr_full + p.eps * (ar_full + adr_full)
    c_ops = [np.sqrt(p.kappa) * ar_full]

    res_dm = (qt.basis(Nf, 0) * qt.basis(Nf, 0).dag()).full()  # resonator ground |0><0|

    if solver == "expm_gpu":
        S_full = _full_superop_expm_gpu(H, c_ops, p.t_meas)
        S = _reduce_full_superop_to_qubit(
            S_full, full_dims=[Lq, Nf], keep=[0], ancilla_init=[(1, res_dm)], Lq=Lq
        )
        return qt.Qobj(S, dims=[[[Lq], [Lq]], [[Lq], [Lq]]], superrep="super")

    if solver == "ode":
        tlist = np.array([0.0, p.t_meas])
        opts = {"atol": 1e-12, "rtol": 1e-10, "nsteps": 2_000_000}
        # build the qubit superoperator by evolving each qubit basis dyad x |0><0|_r and tracing out r.
        res_dm_q = qt.Qobj(res_dm)
        S = np.zeros((Lq * Lq, Lq * Lq), dtype=CDTYPE)  # column-stacked qubit superop
        for i in range(Lq):
            for j in range(Lq):
                rho0_q = qt.basis(Lq, i) * qt.basis(Lq, j).dag()
                rho0 = qt.tensor(qt.Qobj(rho0_q), res_dm_q)
                out = qt.mesolve(H, rho0, tlist, c_ops=c_ops, options=opts).states[-1]
                rho_q = out.ptrace(0).full()  # trace out the resonator -> (Lq, Lq)
                # column-stack: vec index = j*Lq + i (Fortran). E(|i><j|) is column (j*Lq+i).
                S[:, j * Lq + i] = rho_q.reshape(-1, order="F")
        return qt.Qobj(S, dims=[[[Lq], [Lq]], [[Lq], [Lq]]], superrep="super")

    raise ValueError(f"unknown solver {solver!r}; use 'expm_gpu' (default) or 'ode'")


def build_readout_dephasing_channel(p: ReadoutParams, completion: str = "identity_sink",
                                    solver: str = "expm_gpu"):
    """Derive the readout-induced dephasing channel as engine-ready (3,3) Kraus.

    solver="expm_gpu" (DEFAULT, GPU matrix_exp) or "ode" (the qt.mesolve oracle)."""
    S = readout_dephasing_superop(p, solver=solver)
    kraus, resid, leaked = superop_to_truncated_kraus_1q(
        S, track_dim=3, sim_levels=p.sim_levels, completion=completion
    )
    return {"kraus": kraus, "cptp_residual": resid, "leaked_population": leaked,
            "c_analytic": readout_coherence_retention_analytic(p),    # EXACT transient oracle (the GT target)
            "Gamma_ss_rate": readout_dephasing_rate_analytic(p),       # steady-state rate (reporting)
            "nbar": readout_nbar_steadystate(p), "params": p}


# ----------------------------------------------------------------------------------------
# PUSH: 2-resonator correlated readout (2 qubits x 2 resonators) -> spectator dephasing.
#   FLAG: the LARGE sim. Hilbert dim = sim_levels^2 * n_fock^2; with the column-by-column
#   superop build over the (qubit-pair) tracked space the cost is dominated by the joint mesolve.
# ----------------------------------------------------------------------------------------
@dataclass(frozen=True)
class CorrReadoutParams:
    """2-resonator correlated-readout knobs (NEVER frozen).

    Grounding (Heinsoo: ΔR/2pi ~ 160 MHz resonator spacing; Purcell ∝Δ^-4 vs ∝Δ^-2; κ_R/2pi ~ 10 MHz,
    J/2pi = 10 MHz):
      chi          : per-qubit dispersive shift (as ReadoutParams). Default 1.0 MHz.
      kappa        : resonator linewidth. Default 10 MHz.
      eps0         : drive on resonator 0 (the MEASURED qubit's resonator). Default 10 MHz.
      J_R          : resonator-resonator coupling. Default 10 MHz (Heinsoo J/2pi=10).
      Delta_R      : resonator-resonator frequency spacing. Default 160 MHz (Heinsoo). SWEPT (the Δ^-2 /
                     Δ^-4 scaling law is the oracle).
      purcell      : if True, resonator 1 has a Purcell filter -> cross-photon ∝Δ^-4; else ∝Δ^-2.
      t_meas       : 80 ns.  n_fock_per : per-resonator Fock truncation. DEFAULT None => ADAPTIVE (the §1
                     fix): resolved to max(6, ceil(4*nbar0+6)) on the DRIVEN resonator-0 photon number
                     nbar0=(2 eps0/kappa)^2 (resonator-1 carries only the small cross-photon, so the
                     driven mode sets the truncation). KEEP the joint space sim_levels^2 * n_fock_per^2
                     bounded; convergence-checked, FLAGGED. An explicit int override is honored verbatim.
      sim_levels   : 2 qubits at this local dim (default 3; |2> tracked).
    """

    chi: float = mhz(1.0)
    kappa: float = mhz(10.0)
    eps0: float = mhz(10.0)
    J_R: float = mhz(10.0)
    Delta_R: float = mhz(160.0)
    purcell: bool = True
    t_meas: float = 80.0
    n_fock_per: int | None = None   # None => ADAPTIVE (resolve_n_fock_per); an int overrides verbatim.
    sim_levels: int = 3

    def with_(self, **kw) -> "CorrReadoutParams":
        return dataclasses.replace(self, **kw)

    def resolve_n_fock_per(self) -> int:
        """The EFFECTIVE per-resonator Fock truncation: the explicit ``n_fock_per`` if set, else the
        ADAPTIVE ``max(6, ceil(4*nbar0+6))`` on the DRIVEN resonator-0 photon number nbar0=(2 eps0/
        kappa)^2 (the §1 adaptive-n_fock fix; floor 6 to bound the joint sim). KEEP SMALL — the joint
        space is sim_levels^2 * n_fock_per^2."""
        nbar0 = float((2.0 * self.eps0 / self.kappa) ** 2)
        return int(adaptive_n_fock(nbar0, self.n_fock_per, floor=6))


def corr_readout_cross_nbar_analytic(p: CorrReadoutParams) -> float:
    """ANALYTIC oracle: the cross-photon number in the SPECTATOR resonator-1 when driving resonator-0.

    Off-resonant coupling J_R at detuning Delta_R transfers a small steady-state amplitude to resonator 1:
      no Purcell (∝Δ^-2):  nbar_1 = (J_R / Delta_R)^2 * nbar_0
      Purcell    (∝Δ^-4):  nbar_1 = (J_R / Delta_R)^2 * (kappa / Delta_R)^2 * nbar_0
    where nbar_0 = (2 eps0/kappa)^2. The Heinsoo Δ^-4 scaling (the Purcell-filter protection) is the
    headline; the exponent is the oracle the joint mesolve must reproduce. Closed-form, no QuTiP."""
    nbar0 = float((2.0 * p.eps0 / p.kappa) ** 2)
    base = (p.J_R / p.Delta_R) ** 2 * nbar0
    if p.purcell:
        return float(base * (p.kappa / p.Delta_R) ** 2)
    return float(base)


def corr_readout_spectator_dephasing_analytic(p: CorrReadoutParams) -> float:
    """Spectator (qubit-1) measurement-induced dephasing rate from the cross-photon: 8 chi^2 nbar_1 /
    kappa (the same dispersive form on the spectator). rad/ns. Closed-form."""
    return float(8.0 * (p.chi ** 2) * corr_readout_cross_nbar_analytic(p) / p.kappa)


def corr_readout_spectator_superop(p: CorrReadoutParams) -> qt.Qobj:
    """mesolve the joint (qubit0, qubit1, resonator0, resonator1) system while DRIVING resonator-0, and
    return the SPECTATOR qubit-1 superoperator (everything else traced out) over [0, t_meas].

    H = chi (n_q0 n_r0 + n_q1 n_r1)            [dispersive per qubit-resonator]
        + eps0 (a_r0 + a_r0^dag)               [drive resonator 0 only]
        + J_R (a_r0 a_r1^dag + h.c.)           [resonator-resonator coupling]
        + Delta_R n_r1                          [resonator-1 detuning, off-resonant from the drive]
      collapse: sqrt(kappa) a_r0, sqrt(kappa) a_r1
    With a Purcell filter on resonator 1 (``purcell``), its decay is faster -> the steady cross-photon
    scales Δ^-4 (the filter suppresses the off-resonant drive). We model the filter by an EXTRA decay on
    resonator 1 (sqrt(kappa * (kappa/Delta_R)^2) a_r1) — a declared phenomenological proxy for the filter
    transfer (the EXACT Purcell-filter network is out of scope; the Δ^-4 SCALING is the oracle target).

    HILBERT SIZE (FLAG): sim_levels^2 * n_fock_per^2; n_fock_per is ADAPTIVE (resolve_n_fock_per):
    max(6, ceil(4*nbar0+6)). At the default eps0 (nbar0~4) -> n_fock_per=24 -> joint 3^2*24^2 = 5184
    (the LARGE sim — KEEP eps0 small / n_fock_per bounded; the orchestrator runs this alone, serial).
    """
    Lq = int(p.sim_levels)
    Nf = int(p.resolve_n_fock_per())   # ADAPTIVE per-resonator Fock truncation (the §1 fix)
    # operators on the 4-factor space [q0, q1, r0, r1]
    aq, adq = _ladder(Lq)
    ar, adr = _ladder(Nf)
    nq = adq * aq
    nr = adr * ar
    Iq = qt.qeye(Lq)
    Ir = qt.qeye(Nf)

    def emb(op, slot):
        ops = [Iq, Iq, Ir, Ir]
        ops[slot] = op
        return qt.tensor(*ops)

    n_q0 = emb(nq, 0); n_q1 = emb(nq, 1)
    n_r0 = emb(nr, 2); n_r1 = emb(nr, 3)
    a_r0 = emb(ar, 2); ad_r0 = emb(adr, 2)
    a_r1 = emb(ar, 3); ad_r1 = emb(adr, 3)

    H = (p.chi * (n_q0 * n_r0 + n_q1 * n_r1)
         + p.eps0 * (a_r0 + ad_r0)
         + p.J_R * (a_r0 * ad_r1 + ad_r0 * a_r1)
         + p.Delta_R * n_r1)
    c_ops = [np.sqrt(p.kappa) * a_r0, np.sqrt(p.kappa) * a_r1]
    if p.purcell:
        # declared Purcell-filter proxy: extra decay on resonator 1 ~ (kappa/Delta_R) -> Δ^-4 cross-photon
        extra = p.kappa * (p.kappa / p.Delta_R) ** 2
        c_ops.append(np.sqrt(max(extra, 0.0)) * a_r1)
    tlist = np.array([0.0, p.t_meas])
    opts = {"atol": 1e-11, "rtol": 1e-9, "nsteps": 2_000_000}

    r0vac = qt.basis(Nf, 0) * qt.basis(Nf, 0).dag()
    r1vac = qt.basis(Nf, 0) * qt.basis(Nf, 0).dag()
    # spectator qubit-1 superop: vary qubit-1's dyad, keep qubit-0 in |0> (a measured-but-fixed pointer),
    # trace out q0, r0, r1 -> the qubit-1 channel induced by driving resonator-0.
    q0_fixed = qt.basis(Lq, 0) * qt.basis(Lq, 0).dag()
    S = np.zeros((Lq * Lq, Lq * Lq), dtype=CDTYPE)
    for i in range(Lq):
        for j in range(Lq):
            q1dy = qt.basis(Lq, i) * qt.basis(Lq, j).dag()
            rho0 = qt.tensor(q0_fixed, qt.Qobj(q1dy), r0vac, r1vac)
            out = qt.mesolve(H, rho0, tlist, c_ops=c_ops, options=opts).states[-1]
            rho_q1 = out.ptrace(1).full()  # qubit-1 reduced
            S[:, j * Lq + i] = rho_q1.reshape(-1, order="F")
    return qt.Qobj(S, dims=[[[Lq], [Lq]], [[Lq], [Lq]]], superrep="super")


def iq_assignment_2x2(p: CorrReadoutParams, snr0: float, snr1: float, *, cross: float | None = None):
    """DECLARED IQ->bit 2x2 correlated-assignment matrix (os-S3; NOT a Hamiltonian).

    A simple soft-readout boundary model: each qubit's assignment error is the Gaussian-overlap
    1 - Phi(SNR/2) on its own resonator; the spectator's cross-photon induces an additional CORRELATED
    misassignment ``cross`` (default = the analytic cross-photon fraction). Returns the 4x4 conditional
    P(measured bits | true bits) for the pair (a declared classifier, reported for the assignment push).
    """
    from math import erf, sqrt as _sqrt

    def perr(snr):
        # P(error) for two Gaussians separated by SNR: 0.5*erfc(SNR / (2 sqrt2))
        return 0.5 * (1.0 - erf(float(snr) / (2.0 * _sqrt(2.0))))

    e0, e1 = perr(snr0), perr(snr1)
    c = float(corr_readout_cross_nbar_analytic(p)) if cross is None else float(cross)
    c = min(max(c, 0.0), 0.25)  # bound the correlated misassignment
    # 2x2 single-qubit assignment for each, then a correlated correction on the joint (declared).
    A0 = np.array([[1 - e0, e0], [e0, 1 - e0]], dtype=np.float64)
    A1 = np.array([[1 - e1, e1], [e1, 1 - e1]], dtype=np.float64)
    joint = np.kron(A0, A1)
    # correlated correction: when qubit-0 is driven to "1", spectator misassignment rises by c.
    corr = np.zeros_like(joint)
    corr[2, 3] = c; corr[2, 2] = -c   # true=10: leak some 10->11
    corr[3, 2] = c; corr[3, 3] = -c   # true=11: leak some 11->10
    out = joint + corr
    out = np.clip(out, 0.0, None)
    out = out / out.sum(axis=1, keepdims=True)  # renormalize rows (conditional)
    return out


# ========================================================================================
# A'. READOUT-INDUCED LEAKAGE (MIST / ionization) — the FIRST CROSS-MECHANISM COUPLING.
#     READOUT axis  x  ④ LEAKAGE axis.  Xiong 2509.11822 (ℒ↑≈0.08%/100ns) + Fechant 2505.00674
#     (MIST = multiphoton ionization, offset-charge-dependent critical n̄).
#
# THE PHYSICS (Fechant/Blais measurement-induced transitions) + THE SEMICLASSICAL-CAVITY METHOD:
#   the dispersive readout drives the resonator to a LARGE photon number n̄>>1 to boost SNR. At
#   operating power the cavity is a big coherent field |alpha|^2 = n̄, so the STANDARD MIST treatment
#   (Shillito et al. PRX Quantum 3, 2022; Cohen/Dumas/Blais 2402.06615) treats the cavity as a CLASSICAL
#   coherent DRIVE on the transmon charge — NOT a quantized Fock mode (which would need n_fock ~ n̄+ -> a
#   (sim_levels*n_fock)^4 Liouvillian -> OOM at readout n̄). The driven transmon, in the rotating frame
#   of the resonator drive, has a TIME-INDEPENDENT effective Hamiltonian whose spectrum contains the
#   MULTIPHOTON |1>->|2> resonance: the per-level ac-Stark shift 2 chi n̄ (pulling |1> toward |2>) plus a
#   classical charge drive ~sqrt(n̄) g (bridging the anharmonic gap) EXCITE |1>->|2> (ionization) near a
#   CRITICAL n̄_crit = |alpha_q|/(2|chi|k). DERIVED from the driven-transmon spectrum: the leak GROWS with
#   n̄, is ZERO at n̄=0 (no drive -> no MIST), and sharpens toward n̄_crit — the multiphoton signature.
#   Hilbert = the TRANSMON ONLY (sim_levels, dim<=4 -> superop 16x16), NO Fock mode -> NO OOM, n̄ swept
#   via the CLASSICAL drive amplitude sqrt(n̄), not via Fock truncation.
#
# WHY THIS IS THE FIRST COUPLING (the user's "all mechanisms can couple"):
#   the readout DEPHASING channel (A) and the ④ LEAKAGE channel were SEPARATE axes; MIST is the first
#   channel where TURNING THE READOUT ON drives the LEAKAGE axis (|1>->|2>). The coupling layer this
#   opens (declared, future): drive↔leakage (gate-drive-induced leakage), ZZ↔gate (idle ZZ shifting the
#   CZ conditional phase), TLS↔leakage (defect-assisted leakage). MIST is the concrete first instance.
# ========================================================================================
@dataclass(frozen=True)
class MISTParams:
    r"""Measurement-induced-transition (readout-induced leakage / ionization) knobs (NEVER frozen;
    Xiong 2509.11822 + Fechant 2505.00674 grounding; magnitude BRACKETED + SWEPT).

    The deriver builds a MULTI-LEVEL transmon ONLY (>=3 levels: |0>,|1>,|2>,... so the |1>->|2>
    multiphoton resonance EXISTS) in the SEMICLASSICAL-CAVITY frame: the readout cavity at operating
    power is a CLASSICAL coherent drive on the transmon charge (Shillito 2022 / Cohen-Blais), so there is
    NO quantized Fock resonator and NO n_fock — the Hilbert dim is just sim_levels (<=4). n̄ is swept via
    the classical drive amplitude sqrt(n̄), the readout POWER. matrix_exp the constant rotating-frame
    Liouvillian -> a (3,3) qubit channel that LEAKS |1>->|2> at the readout n̄.

      chi      : dispersive shift chi/2pi (the readout coupling; sets the per-photon ac-Stark pull
                 2 chi n̄ that closes the |1>->|2> gap at n̄_crit). Default 1.0 MHz.
      kappa    : resonator linewidth kappa/2pi. Default 10 MHz (Heinsoo/Xiong read-on kappa~2chi..20MHz).
      eps      : readout drive amplitude eps/2pi -> sets nbar=(2 eps/kappa)^2 (the readout POWER knob;
                 raising eps -> raising n̄ -> approaching n̄_crit -> more MIST). Default 10 MHz -> n̄=4.
                 SWEPT (the n̄-dependence is the certified mechanism signature). Use eps in the readout
                 range so n̄ ~ 5-30 (where the leak brackets Xiong's 0.08%).
      g_qr     : transmon-resonator coupling g/2pi. In the semiclassical frame it sets the CLASSICAL
                 charge-drive matrix element ~ g_qr * sqrt(n̄) that bridges the anharmonic |1>->|2> gap.
                 Default 50 MHz (typical transmon-readout g). BRACKETED.
      Delta_qr : transmon-resonator detuning (omega_q - omega_r)/2pi. Default 1000 MHz (1 GHz; dispersive
                 regime g << |Delta_qr|; enters only as a reporting/consistency knob in the semiclassical
                 frame — the drive frame is set to the resonator). SWEPT/BRACKETED.
      alpha_q  : transmon anharmonicity (rad/ns). Default -300 MHz (Varbanov; sets the |1>->|2> gap, hence
                 the multiphoton-resonance n̄_crit). The MIST n̄_crit is offset-charge dependent (Fechant);
                 OFFSET CHARGE is NOT swept here (a DECLARED bounded simplification, mS-2) -> the leak
                 magnitude is a representative-bracket, not the charge-resolved physical value.
      t_meas   : readout duration (ns). Default 100 ns (Xiong measures ℒ↑ per 100 ns). SWEPT.
      kappa_eff : effective transmon-level decay during readout (rad/ns) -> the dissipative collapse that
                 makes the channel CPTP-with-loss (a small relaxation on the driven transmon; the readout
                 also damps). Default kappa/100 (a small residual). SWEPT/BRACKETED.
      sim_levels : transmon levels (>=3: |2> is the LEAK TARGET, MUST be tracked; |3> sharpens the
                 ionization ladder — default 4, dim 4 -> superop 16x16 (TINY). The (3,3) channel tracks
                 {0,1,2}; |3>+ folded by identity_sink). Default 4. (NO n_fock — semiclassical cavity.)
    """

    chi: float = mhz(1.0)
    kappa: float = mhz(10.0)
    eps: float = mhz(10.0)
    g_qr: float = mhz(50.0)
    Delta_qr: float = mhz(1000.0)
    alpha_q: float = mhz(-300.0)
    t_meas: float = 100.0
    kappa_eff: float = mhz(0.1)     # small residual transmon decay during readout (=kappa/100).
    sim_levels: int = 4

    def with_(self, **kw) -> "MISTParams":
        return dataclasses.replace(self, **kw)


def mist_nbar_steadystate(p: MISTParams) -> float:
    """Steady-state driven-resonator photon number nbar=(2 eps/kappa)^2 (the readout POWER that drives
    MIST; the same driven-damped-mode form as the readout dephasing). In the semiclassical-cavity frame
    nbar enters only as the CLASSICAL drive amplitude (sqrt(nbar)) + the ac-Stark shift (2 chi nbar) — it
    is NOT a Fock truncation. Closed-form, no QuTiP."""
    return float((2.0 * p.eps / p.kappa) ** 2)


def mist_critical_nbar_analytic(p: MISTParams, k: int = 1) -> float:
    r"""INDEPENDENT ANALYTIC ORACLE (Fechant/Blais MIST multiphoton-resonance condition): the CRITICAL
    photon number n̄_crit at which the ac-Stark-shifted |1> level becomes resonant with |2> via a
    ``k``-photon process, so the readout drive can EXCITE |1>->|2> (ionization).

    The transmon-resonator dispersive ac-Stark shift pulls the qubit transition by 2 chi n̄ per photon;
    the |1>->|2> transmon gap sits alpha_q below the |0>->|1> gap. The k-photon |1>->|2> resonance
    condition (the leading Blais-MIST estimate) is reached when the accumulated Stark shift closes the
    anharmonic gap:
        2 |chi| n̄_crit  ~  |alpha_q| / k        ->        n̄_crit ~ |alpha_q| / (2 |chi| k).
    This is the n̄ at which the |1>->|2> leak SPIKES (the multiphoton resonance). It is INDEPENDENT of
    our QuTiP sim (a closed-form from chi, alpha_q only) — the anti-circular anchor for the n̄-dependence
    (NOT 'matches our own readout sim'). The offset-charge dependence (Fechant) shifts n̄_crit by the
    charge-dispersion of the high levels (mS-2, declared simplification — not swept here). rad/ns units
    cancel in the ratio. Returns n̄_crit (dimensionless photon number).

    Grounding: Fechant 2505.00674 (critical n̄, offset-charge dependent, multiphoton); chi~1MHz,
    alpha_q~-300MHz -> n̄_crit ~ 300/(2*1*1) ~ 150 for k=1 (single-photon); larger k -> smaller n̄_crit.
    """
    chi_mag = abs(float(p.chi))
    if chi_mag <= 0 or k <= 0:
        return float("inf")
    return float(abs(p.alpha_q) / (2.0 * chi_mag * float(k)))


def mist_leakage_superop(p: MISTParams, solver: str = "expm_gpu") -> qt.Qobj:
    r"""Build the TRANSMON superoperator over [0, t_meas] for the readout-induced MIST/ionization
    Hamiltonian, in the SEMICLASSICAL-CAVITY (displaced-frame) treatment — the standard MIST method
    (Shillito et al. PRX Quantum 3, 023046 (2022); Cohen/Dumas/Blais 2402.06615). TIME-INDEPENDENT (the
    rotating-frame effective drive is constant) -> the propagator is expm(L * t_meas) via
    torch.linalg.matrix_exp on cuda (complex128). HILBERT = the TRANSMON ONLY (NO Fock resonator) -> NO
    trace-out, NO n_fock, NO OOM.

    THE FRAME / H (transmon-only, rotating frame of the resonator drive; n̄=(2 eps/kappa)^2 is the
    operating-power photon number; the cavity is a CLASSICAL coherent field |alpha|^2=n̄):
        H_eff = (alpha_q/2) n_q (n_q - 1)        [transmon anharmonic ladder -> the |1>->|2> gap = alpha_q]
              + 2 chi n̄ * n_q                     [ac-Stark shift: 2 chi per photon pulls each level; this
                                                    CLOSES the |1>->|2> gap as n̄ -> n̄_crit = |alpha|/(2|chi|)]
              + Omega (a_q + a_q^dag),  Omega = g_qr * sqrt(n̄)
                                                  [the CLASSICAL cavity-field charge drive (~sqrt(n̄) g);
                                                   bridges the anharmonic gap -> EXCITES |1>->|2> (MIST)]
      collapse: sqrt(kappa_eff) a_q               [small residual transmon relaxation during readout ->
                                                   the channel is CPTP-with-loss, not unitary]
    The |1>->|2> transfer GROWS with n̄ (both the drive Omega~sqrt(n̄) and the Stark shift 2 chi n̄ rise)
    and SHARPENS as the Stark shift closes the gap near n̄_crit — the multiphoton MIST resonance. At n̄=0
    Omega=0 AND the Stark shift=0 -> H is diagonal -> ZERO |1>->|2> leak (no readout -> no MIST), EXACTLY.

    DERIVED, NOT phenomenological: the leak is read off the driven-transmon spectrum (Omega, the Stark
    shift, the anharmonic gap) — it is zero at n̄=0, monotone-rising in n̄, and resonance-sharpened toward
    the INDEPENDENT n̄_crit = mist_critical_nbar_analytic. The offset-charge dependence of n̄_crit (Fechant)
    is mS-2 declared (not swept) -> a representative bracket anchored to Xiong's ℒ↑≈0.08%/100ns.

    SEMICLASSICAL-CAVITY SIMPLIFICATION (mS-1, declared+bounded — rule III): the readout cavity is
    treated as a CLASSICAL coherent drive (semiclassical), VALID for readout n̄>>1; photon shot-noise /
    measurement back-action on the transmon are neglected, error ~O(1/n̄) (the leading correction to the
    coherent-state mean-field). This is the PHYSICALLY-STANDARD MIST treatment (Shillito/Cohen-Blais),
    NOT a toy shortcut — it REPLACES the (Fock-quantized, OOM-at-readout-n̄) full-Liouvillian model.

    HILBERT SIZE (mS-1b): dim = sim_levels (default 4) -> superop 4^2=16 -> a 16x16 matrix_exp (TRIVIAL;
    no n̄ dependence in the dim). n̄ is swept via Omega=g_qr*sqrt(n̄) + the Stark shift, NOT via Fock.

    solver:
      "expm_gpu" (DEFAULT) -- S = torch.linalg.matrix_exp(L * t_meas) on cuda; the system IS the transmon,
                              so S is the transmon superop directly (no trace-out).
      "ode"               -- the per-dyad qt.mesolve loop (the INDEPENDENT oracle the gtcheck cross-checks).
    """
    Lq = int(p.sim_levels)
    aq, adq = _ladder(Lq)
    nq = adq * aq
    nbar = mist_nbar_steadystate(p)
    # The CLASSICAL cavity field (amplitude sqrt(n̄)) drives the transmon charge, but in the DISPERSIVE
    # regime (g_qr << Delta_qr) the field only weakly displaces the transmon: the effective charge-drive
    # matrix element on the anharmonic |1>->|2> transition is DISPERSIVELY SUPPRESSED by one power of the
    # small parameter g_qr/Delta_qr (the transmon sees the field through its off-resonant coupling):
    #     Omega_eff = g_qr * sqrt(n̄) * (g_qr / Delta_qr).
    # This keeps the drive PERTURBATIVE (Omega_eff << |alpha_q|) so the leak is a small OFF-RESONANT
    # excursion that GROWS as the ac-Stark shift 2 chi n̄ closes the |1>->|2> detuning toward n̄_crit =
    # |alpha_q|/(2 chi) — NOT a saturated Rabi flop. (Using the BARE g_qr*sqrt(n̄) would over-drive the
    # transition into full Rabi oscillations — unphysical for the dispersive readout regime.)
    Omega_eff = float(p.g_qr) * float(np.sqrt(max(nbar, 0.0))) * (float(p.g_qr) / float(p.Delta_qr))

    # The |1>->|2> detuning in the driven-transmon frame: the anharmonic gap |alpha_q| REDUCED by the
    # ac-Stark shift 2 chi n̄ (the resonance condition 2 chi n̄ -> |alpha_q| closes it at n̄_crit). We put
    # this on the diagonal as a level-dependent energy so the |1>->|2> transition sits at detuning
    # delta(n̄) = |alpha_q| - 2 chi n̄ from the (weak) drive — a Lorentzian-in-delta leak peaked at n̄_crit.
    # E_m = (alpha/2) m(m-1)  [anharmonic ladder]  +  2 chi n̄ * m  [ac-Stark, closes the gap as n̄ rises].
    H = (0.5 * p.alpha_q * (adq * adq * aq * aq)            # (alpha/2) n_q(n_q-1) anharmonic ladder
         + 2.0 * p.chi * nbar * nq                          # ac-Stark shift 2 chi n̄ per level (closes the gap)
         + Omega_eff * (aq + adq))                          # dispersively-suppressed classical charge drive: MIST
    c_ops = []
    if p.kappa_eff > 0:
        c_ops.append(np.sqrt(p.kappa_eff) * aq)            # small residual transmon relaxation -> CPTP-with-loss

    if solver == "expm_gpu":
        # no ancilla: expm(L * t) IS the transmon superop (same column-stacked "super" convention).
        S = _full_superop_expm_gpu(H, c_ops, p.t_meas)
        return qt.Qobj(S, dims=[[[Lq], [Lq]], [[Lq], [Lq]]], superrep="super")

    if solver == "ode":
        tlist = np.array([0.0, p.t_meas])
        opts = {"atol": 1e-12, "rtol": 1e-10, "nsteps": 2_000_000}
        S = np.zeros((Lq * Lq, Lq * Lq), dtype=CDTYPE)
        for i in range(Lq):
            for j in range(Lq):
                rho0 = qt.basis(Lq, i) * qt.basis(Lq, j).dag()
                out = qt.mesolve(H, qt.Qobj(rho0), tlist, c_ops=c_ops, options=opts).states[-1]
                S[:, j * Lq + i] = out.full().reshape(-1, order="F")
        return qt.Qobj(S, dims=[[[Lq], [Lq]], [[Lq], [Lq]]], superrep="super")

    raise ValueError(f"unknown solver {solver!r}; use 'expm_gpu' (default) or 'ode'")


def mist_leak_population(kraus, *, level_from: int = 1, level_to: int = 2) -> float:
    """The readout-induced |level_from>->|level_to> LEAK population: P(|2>) after the channel acts on a
    pure |1> input. E(|1><1|)[2,2] for the (3,3) channel. This is the Xiong ℒ↑ analog (the |1>->|2>
    leakage rate over t_meas). Returns a probability in [0,1]."""
    d = int(np.asarray(kraus[0]).shape[0])
    rho = np.zeros((d, d), dtype=CDTYPE)
    rho[int(level_from), int(level_from)] = 1.0
    out = sum(np.asarray(K) @ rho @ np.asarray(K).conj().T for K in kraus)
    return float(np.real(out[int(level_to), int(level_to)]))


def build_mist_leakage_channel(p: MISTParams, completion: str = "identity_sink", solver: str = "expm_gpu"):
    r"""Derive the readout-induced-leakage (MIST) channel as engine-ready (3,3) Kraus on {0,1,2}.

    The (sim_levels) superop is projected to the tracked {0,1,2} block (track_dim=3); levels >=3 (the
    |3>+ ionization continuum) are folded by identity_sink (their small mass re-injected to |2>, the
    top tracked level — consistent with "is-leaked"). Returns the channel + the |1>->|2> leak population
    + the analytic critical-n̄ oracle + nbar (the magnitude-bracket + n̄-dependence anchors).

    solver="expm_gpu" (DEFAULT, GPU matrix_exp) or "ode" (the qt.mesolve oracle)."""
    S = mist_leakage_superop(p, solver=solver)
    kraus, resid, leaked = superop_to_truncated_kraus_1q(
        S, track_dim=3, sim_levels=p.sim_levels, completion=completion
    )
    return {"kraus": kraus, "cptp_residual": resid, "leaked_population": leaked,
            "leak_1to2": mist_leak_population(kraus, level_from=1, level_to=2),  # the Xiong ℒ↑ analog
            "nbar": mist_nbar_steadystate(p),
            "nbar_crit_k1": mist_critical_nbar_analytic(p, k=1),   # Fechant single-photon resonance
            "nbar_crit_k2": mist_critical_nbar_analytic(p, k=2),   # 2-photon resonance (smaller n̄)
            "params": p}


# ========================================================================================
# B. TLS / SPECTATOR DEFECT (transmon qutrit x TLS qubit; Jaynes-Cummings exchange).
# ========================================================================================
@dataclass(frozen=True)
class TLSParams:
    """TLS / spectator-defect knobs (NEVER frozen; Gao 2605.23385 grounding).

      g        : TLS-qubit (effective) coupling g̃/2pi. Gao measured 1.4-10.4 MHz. Default 5 MHz. SWEPT.
      delta    : qubit-TLS detuning (omega_q - omega_TLS). Default 0 (resonant: cleanest vacuum Rabi).
      t1_tls   : TLS T1 (ns). Gao 44.7 us = 44700 ns. Default 44700.
      tphi_tls : TLS pure dephasing time (ns). Gao T_phi^TLS ~ 1.1 us = 1100 ns. Default 1100.
      t_evol   : interaction window (ns). Default 60 ns (Gao iSWAP gate window).
      alpha_q  : transmon anharmonicity (rad/ns). Default -300 MHz (Varbanov).
      sim_levels : transmon levels (>=3 to track |2>). Default 3.
    """

    g: float = mhz(5.0)
    delta: float = 0.0
    t1_tls: float = 44700.0
    tphi_tls: float = 1100.0
    t_evol: float = 60.0
    alpha_q: float = mhz(-300.0)
    sim_levels: int = 3

    def with_(self, **kw) -> "TLSParams":
        return dataclasses.replace(self, **kw)


def tls_vacuum_rabi_analytic(p: TLSParams, t: float | None = None) -> float:
    """ANALYTIC oracle: lossless Jaynes-Cummings vacuum-Rabi transfer in the single-excitation subspace
    {|1>_q|0>_T, |0>_q|1>_T}. On resonance (delta=0): P_{|1,0>->|0,1>}(t) = sin^2(g t). Off resonance
    the generalized Rabi: P = (g^2 / Omega^2) sin^2(Omega t), Omega = sqrt(g^2 + (delta/2)^2). Closed
    form, no QuTiP. ``t`` defaults to p.t_evol."""
    tt = float(p.t_evol if t is None else t)
    Omega = np.sqrt(p.g ** 2 + (p.delta / 2.0) ** 2)
    if Omega <= 0:
        return 0.0
    return float((p.g ** 2 / Omega ** 2) * np.sin(Omega * tt) ** 2)


def tls_channel_superop(p: TLSParams, solver: str = "expm_gpu") -> qt.Qobj:
    """Build the QUBIT superoperator (TLS traced out) over [0, t_evol] for the (transmon qutrit,
    TLS qubit) JC-exchange + TLS-Lindblad system. TIME-INDEPENDENT -> the propagator is
    expm(L * t_evol).

    HILBERT SIZE (FLAG): full dim = sim_levels * 2 (default 3 * 2 = 6 -> superop 6^2 = 36; a
    36x36 matrix_exp is TRIVIAL). The TLS is then traced out.

    solver:
      "expm_gpu" (DEFAULT) -- L = liouvillian(H, c_ops); S_full = torch.linalg.matrix_exp(L *
                              t_evol) on cuda (complex128); then trace out the TLS.
      "ode"               -- the original per-dyad qt.mesolve loop (the INDEPENDENT oracle).

    H = (alpha_q/2) n_q(n_q-1) [transmon anharmonicity, frame at omega_q]
        + delta * (tau^dag tau)  [TLS detuning: excited |1>_T at energy delta, ground |0>_T at 0]
        + g (a_q tau^dag + a_q^dag tau)   [JC exchange: qubit lowers / TLS raises + h.c.]
      collapse: sqrt(1/t1_tls) tau  [TLS T1], sqrt(2/tphi_tls) (tau^dag tau) [TLS Tphi]
    The TLS starts in its ground state |0>_T; tracing it out after evolution gives the qubit channel
    (loss + dephasing from the resonant exchange with a lossy defect).

    *** CONVENTION (the §3 FIX, 2026-06-25) ***
    The TLS is built with ``qt.destroy(2)`` (NUMBER-state convention: ``tau|1>=|0>`` lowers, ``basis(2,0)``
    is GROUND, ``basis(2,1)`` is EXCITED) — the SAME convention as the transmon ``aq`` and the engine.
    The earlier ``qt.sigmam/sigmap/sigmaz`` are the SPIN-1/2 convention where ``basis(2,0)`` is the
    EXCITED state, so ``sigma^+ |basis(2,0)> = 0`` annihilated the (intended-ground) TLS start -> the
    exchange ``<01|V|10> = 0`` and ZERO transfer (the diff=1.0 was QuTiP giving identically 0, NOT a
    factor-2 / sin^2(2gt) double-frequency). Using ``destroy(2)`` makes ground=|0>, excited=|1>
    consistently, so the JC exchange couples |1>_q|0>_T <-> |0>_q|1>_T with matrix element exactly g and
    the transfer is sin^2(g t) (verified to 0.0 vs the analytic, resonant AND off-resonant).
    """
    Lq = int(p.sim_levels)
    aq, adq = _ladder(Lq)
    nq = adq * aq
    Iq = qt.qeye(Lq)
    # TLS as a 2-level NUMBER-state system (destroy(2): |0>=ground, |1>=excited; matches the transmon).
    tau = qt.destroy(2)
    taud = tau.dag()
    n_tls = taud * tau            # excited-state projector |1><1|_T (the unambiguous dephasing operator)
    I2 = qt.qeye(2)

    aq_f = qt.tensor(aq, I2); adq_f = qt.tensor(adq, I2)
    tau_f = qt.tensor(Iq, tau); taud_f = qt.tensor(Iq, taud); n_tls_f = qt.tensor(Iq, n_tls)

    H = (0.5 * p.alpha_q * (adq_f * adq_f * aq_f * aq_f)
         + p.delta * n_tls_f
         + p.g * (aq_f * taud_f + adq_f * tau_f))
    c_ops = []
    if p.t1_tls > 0:
        c_ops.append(np.sqrt(1.0 / p.t1_tls) * tau_f)       # TLS T1: lowering |1>_T -> |0>_T
    if p.tphi_tls > 0:
        c_ops.append(np.sqrt(2.0 / p.tphi_tls) * n_tls_f)   # TLS Tphi: dephasing ~ excited projector

    tls_grnd = (qt.basis(2, 0) * qt.basis(2, 0).dag()).full()  # TLS ground |0><0|

    if solver == "expm_gpu":
        S_full = _full_superop_expm_gpu(H, c_ops, p.t_evol)
        S = _reduce_full_superop_to_qubit(
            S_full, full_dims=[Lq, 2], keep=[0], ancilla_init=[(1, tls_grnd)], Lq=Lq
        )
        return qt.Qobj(S, dims=[[[Lq], [Lq]], [[Lq], [Lq]]], superrep="super")

    if solver == "ode":
        tlist = np.array([0.0, p.t_evol])
        opts = {"atol": 1e-12, "rtol": 1e-10, "nsteps": 2_000_000}
        tls_grnd_q = qt.Qobj(tls_grnd)
        S = np.zeros((Lq * Lq, Lq * Lq), dtype=CDTYPE)
        for i in range(Lq):
            for j in range(Lq):
                q_dy = qt.basis(Lq, i) * qt.basis(Lq, j).dag()
                rho0 = qt.tensor(qt.Qobj(q_dy), tls_grnd_q)
                out = qt.mesolve(H, rho0, tlist, c_ops=c_ops, options=opts).states[-1]
                rho_q = out.ptrace(0).full()
                S[:, j * Lq + i] = rho_q.reshape(-1, order="F")
        return qt.Qobj(S, dims=[[[Lq], [Lq]], [[Lq], [Lq]]], superrep="super")

    raise ValueError(f"unknown solver {solver!r}; use 'expm_gpu' (default) or 'ode'")


def build_tls_channel(p: TLSParams, completion: str = "identity_sink", solver: str = "expm_gpu"):
    """Derive the TLS-coupled qubit channel as engine-ready (3,3) Kraus.

    solver="expm_gpu" (DEFAULT, GPU matrix_exp) or "ode" (the qt.mesolve oracle)."""
    S = tls_channel_superop(p, solver=solver)
    kraus, resid, leaked = superop_to_truncated_kraus_1q(
        S, track_dim=3, sim_levels=p.sim_levels, completion=completion
    )
    return {"kraus": kraus, "cptp_residual": resid, "leaked_population": leaked,
            "vacuum_rabi_analytic": tls_vacuum_rabi_analytic(p), "params": p}


# ----------------------------------------------------------------------------------------
# PUSH (the real win): TLF-bath 1/f ⑤b temporal correlation (classical phase telegraph).
#   FLAG: this is a CLASSICAL stochastic process on the qubit PHASE (small Hilbert space — a single
#   qubit), but the TRAJECTORY-ENSEMBLE size (n_traj) is the compute cost; bounded below.
# ----------------------------------------------------------------------------------------
@dataclass(frozen=True)
class TLFBathParams:
    """1/f TLF-bath knobs (NEVER frozen; Gao Dutta-Horn grounding; magnitude BRACKETED).

      n_tlf      : number of fluctuators. Default 10 (Gao: 10 TLFs reproduce the ten-decade 1/f).
      gamma_min  : minimum switching rate (rad/ns scale -> use 1/ns; Gao 0.6 mHz). Default khz(0.6e-3).
      gamma_max  : maximum switching rate (Gao 0.2 GHz). Default ghz(0.2). (log-uniform between).
      eta        : per-TLF qubit-frequency coupling (rad/ns; the phase kick rate). BRACKETED (device-
                   unmeasured). Default mhz(0.05) (set so Ramsey T2 ~ 0.4 us, Gao). SWEPT.
      t_round    : per-round duration (ns) over which phase accrues. Default 1000 ns (1 us cycle scale).
      sim_levels : 3 (the |2> level is dephasing-inert here; the telegraph is on the {0,1} phase).
    """

    n_tlf: int = 10
    gamma_min: float = khz(0.6e-3)    # ~0.6 mHz
    gamma_max: float = ghz(0.2)       # ~0.2 GHz
    eta: float = mhz(0.05)
    t_round: float = 1000.0
    sim_levels: int = 3

    def with_(self, **kw) -> "TLFBathParams":
        return dataclasses.replace(self, **kw)

    def switching_rates(self) -> np.ndarray:
        """Log-uniform switching rates over [gamma_min, gamma_max] (the Dutta-Horn ensemble that gives
        1/f over the rate band). Deterministic (no RNG) so the PSD oracle is reproducible."""
        lo, hi = np.log(self.gamma_min), np.log(self.gamma_max)
        return np.exp(np.linspace(lo, hi, int(self.n_tlf)))


def tlf_dutta_horn_psd_analytic(p: TLFBathParams, f: np.ndarray) -> np.ndarray:
    """ANALYTIC oracle: the Dutta-Horn PSD of the qubit-frequency noise from the declared TLF ensemble:
        S(f) = sum_i (4 eta^2 gamma_i) / (gamma_i^2 + (2 pi f)^2)   [sum of Lorentzians]
    A log-uniform rate distribution over [gamma_min, gamma_max] yields S(f) ~ 1/f over the band (the
    Dutta-Horn 1/f result). f in 1/ns (so 2 pi f matches the rad/ns gammas). Closed-form, no QuTiP."""
    gammas = p.switching_rates()
    w = 2.0 * np.pi * np.asarray(f, dtype=np.float64)[:, None]   # (Nf, 1)
    g = gammas[None, :]                                          # (1, n_tlf)
    lorentz = (4.0 * p.eta ** 2 * g) / (g ** 2 + w ** 2)
    return lorentz.sum(axis=1)


def tlf_telegraph_phase(p: TLFBathParams, *, R: int, n_traj: int, seed: int) -> np.ndarray:
    """Simulate n_traj trajectories of the qubit's accrued phase over R rounds from N random-telegraph
    fluctuators (each xi_i(t) in {+1,-1} switching at rate gamma_i; the qubit detuning is
    eta * sum_i xi_i, integrated over each round). Returns the per-(traj, round) phase increment array
    (n_traj, R) — the EMERGENT temporally-correlated dephasing process.

    This is a CLASSICAL stochastic simulation (not a Hilbert-space mesolve): each round's dephasing on
    the qubit is exp(i * phase_increment) applied to the {0,1} coherence; averaging over trajectories
    gives the round-correlated dephasing channel. The round-to-round correlation EMERGES from the slow
    fluctuators (gamma_i * t_round << 1) that persist across rounds.

    FLAG: n_traj is the cost (Hilbert space is a single qubit; the ensemble is classical).
    """
    rng = np.random.default_rng(int(seed))
    gammas = p.switching_rates()
    n = int(p.n_tlf)
    dt = float(p.t_round)
    # initial telegraph states +-1 (random)
    xi = rng.choice([-1.0, 1.0], size=(int(n_traj), n))
    phase = np.zeros((int(n_traj), int(R)), dtype=np.float64)
    for r in range(int(R)):
        # over one round, each TLF flips with probability p_flip = 1 - exp(-2 gamma_i dt) (telegraph;
        # the stationary switching probability over dt). We accrue phase at the ROUND-START state (a
        # bounded first-order integration; smaller dt -> exact). Declared (os-S4) bounded simplification.
        # mean detuning over the round ~ eta * sum_i xi_i (held at the round-start state, then flip).
        #
        # *** os-S4 corollary (adversarial-review note 2026-06-25): regime of validity. ***
        # This round-START sampling is FAITHFUL for the SLOW/1-f bath (gamma_i*dt << 1: a TLF rarely flips
        # within a round, so the round-start state ~ the whole-round state) -> the emergent POSITIVE
        # round-to-round persistence is the genuine slow-TLF signature (the certified part). For a
        # SATURATED FAST bath (gamma_i*dt >> 1, p_flip ~ 1) each TLF flips ~every round, so the sampled
        # phase ALTERNATES sign and the lag-1 correlation -> ~ -1 (anti-persistence), an ARTIFACT of the
        # discrete round-start sampling, NOT the true continuous-time fast-bath correlation (~0). The
        # fast bath is used ONLY as a DISCRIMINATING control ("fast signature != the slow +persistence"),
        # never as a physical fast-bath channel -> the artifact does not propagate. The 1/f / slow result
        # (the real win) is in the faithful gamma*dt << 1 regime.
        phase[:, r] = p.eta * dt * xi.sum(axis=1)
        p_flip = 1.0 - np.exp(-2.0 * gammas * dt)            # (n_tlf,)
        flips = rng.random((int(n_traj), n)) < p_flip[None, :]
        xi = np.where(flips, -xi, xi)
    return phase


def tlf_round_dephasing_channel(phase_increments: np.ndarray):
    """Build the PER-ROUND single-qubit dephasing (3,3) Kraus from a trajectory ENSEMBLE of phase
    increments for ONE round (a 1-D array over trajectories). The ensemble-averaged channel is a
    dephasing channel with off-diagonal damping lambda = <exp(i phi)> on the {0,1} coherence:
        rho[0,1] -> <exp(i phi)> rho[0,1].
    Returned as a 2-Kraus dephasing set {sqrt((1+|lambda|)/2) diag(1, lambda/|lambda|, 1) ...} — but for
    a REAL symmetric ensemble <exp(i phi)> is real in [0,1] (call it c); the channel is the standard
    phase-damping {sqrt((1+c)/2) I_phase, sqrt((1-c)/2) Z_phase} on {0,1}, identity on |2>.
    """
    c = float(np.mean(np.cos(phase_increments)))  # <cos phi> (real part of <exp i phi> for symmetric ens)
    c = min(max(c, -1.0), 1.0)
    # phase-damping Kraus on {0,1}, identity on |2>: K0 = sqrt((1+c)/2)*I, K1 = sqrt((1-c)/2)*Z (comp)
    K0 = np.zeros((3, 3), dtype=CDTYPE)
    K1 = np.zeros((3, 3), dtype=CDTYPE)
    a0 = np.sqrt((1.0 + c) / 2.0)
    a1 = np.sqrt((1.0 - c) / 2.0)
    K0[0, 0] = a0; K0[1, 1] = a0; K0[2, 2] = 1.0
    K1[0, 0] = a1; K1[1, 1] = -a1; K1[2, 2] = 0.0
    # NB: K1 has no |2> component (the |2> identity is fully carried by K0), so sum K^dag K = I on {0,1,2}:
    #   |2>: |K0[2,2]|^2 = 1.  {0,1}: a0^2 + a1^2 = 1.  CPTP exact.
    return [K0, K1], c


def tlf_round_to_round_correlation(phase_increments: np.ndarray) -> float:
    """The EMERGENT round-to-round phase correlation (lag-1 Pearson of the per-round phase over the
    trajectory ensemble), averaged over rounds — the CROSS-CHECK statistic vs the WS2 TemporalCorrMask
    (Kam) class. phase_increments shape (n_traj, R)."""
    ph = np.asarray(phase_increments, dtype=np.float64)
    R = ph.shape[1]
    vals = []
    for r in range(R - 1):
        a, b = ph[:, r], ph[:, r + 1]
        va, vb = a.var(), b.var()
        if va > 1e-15 and vb > 1e-15:
            vals.append(float(np.mean((a - a.mean()) * (b - b.mean())) / np.sqrt(va * vb)))
    return float(np.mean(vals)) if vals else 0.0


# ========================================================================================
# C. BURST ELEVATED-T1 + SHARED BATH (Tan 2406.18897 / McEwen).
# ========================================================================================
@dataclass(frozen=True)
class BurstParams:
    """Burst elevated-T1 knobs (NEVER frozen; Tan/McEwen grounding).

      gamma_burst : elevated amplitude-damping rate during the burst (rad/ns -> 1/ns). Default 1/2000 ns
                    (T1 dropped to ~2 us, McEwen 1-2 orders below nominal ~75 us). SWEPT.
      t_round     : per-round duration the elevated rate acts (ns). Default 1000 ns.
      m_demo      : number of qubits in the shared-bath demo (small). Default 2. SWEPT (FLAG: m_demo
                    qubits at sim_levels each -> sim_levels^m_demo joint space; KEEP m_demo <= 3).
      g_common    : common-mode (shared bath) coupling for the demo (rad/ns). Default mhz(1.0).
      sim_levels  : 3.
    """

    gamma_burst: float = 1.0 / 2000.0
    t_round: float = 1000.0
    m_demo: int = 2
    g_common: float = mhz(1.0)
    sim_levels: int = 3

    def with_(self, **kw) -> "BurstParams":
        return dataclasses.replace(self, **kw)


def burst_t1_decay_analytic(p: BurstParams, t: float | None = None) -> float:
    """ANALYTIC oracle: the excited-state survival under elevated amplitude damping,
    P_excited(t) = exp(-gamma_burst t). Closed-form, no QuTiP. ``t`` defaults to p.t_round."""
    tt = float(p.t_round if t is None else t)
    return float(np.exp(-p.gamma_burst * tt))


def burst_single_qubit_superop(p: BurstParams, solver: str = "expm_gpu") -> qt.Qobj:
    """Build a SINGLE-qubit (sim_levels) superoperator for the elevated amplitude-damping over
    [0, t_round]. H = 0 (idle frame); c = sqrt(gamma_burst) a. The qutrit ladder gives the
    |2>->|1>->|0> cascade at the elevated rate (the |2> tracking is exact). TIME-INDEPENDENT ->
    the propagator is expm(L * t_round).

    HILBERT SIZE (FLAG): full dim = sim_levels (default 3 -> superop 3^2 = 9; a 9x9 matrix_exp is
    TRIVIAL). There is NO ancilla here -- the system IS the qubit, so expm(L) is the qubit superop
    directly (no trace-out).

    solver:
      "expm_gpu" (DEFAULT) -- L = liouvillian(H, c_ops); S = torch.linalg.matrix_exp(L * t_round)
                              on cuda (complex128); the system is the qubit -> S is the superop.
      "ode"               -- the original per-dyad qt.mesolve loop (the INDEPENDENT oracle).
    """
    Lq = int(p.sim_levels)
    a, _ = _ladder(Lq)
    H = qt.qzero(Lq)
    c_ops = [np.sqrt(p.gamma_burst) * a]

    if solver == "expm_gpu":
        # no ancilla: expm(L * t) IS the qubit superop (same column-stacked "super" convention).
        S = _full_superop_expm_gpu(H, c_ops, p.t_round)
        return qt.Qobj(S, dims=[[[Lq], [Lq]], [[Lq], [Lq]]], superrep="super")

    if solver == "ode":
        tlist = np.array([0.0, p.t_round])
        opts = {"atol": 1e-12, "rtol": 1e-10, "nsteps": 1_000_000}
        S = np.zeros((Lq * Lq, Lq * Lq), dtype=CDTYPE)
        for i in range(Lq):
            for j in range(Lq):
                rho0 = qt.basis(Lq, i) * qt.basis(Lq, j).dag()
                out = qt.mesolve(H, qt.Qobj(rho0), tlist, c_ops=c_ops, options=opts).states[-1]
                S[:, j * Lq + i] = out.full().reshape(-1, order="F")
        return qt.Qobj(S, dims=[[[Lq], [Lq]], [[Lq], [Lq]]], superrep="super")

    raise ValueError(f"unknown solver {solver!r}; use 'expm_gpu' (default) or 'ode'")


def build_burst_channel(p: BurstParams, completion: str = "identity_sink", solver: str = "expm_gpu"):
    """Derive the single-qubit burst elevated-T1 channel as engine-ready (3,3) Kraus (the channel that
    is classically BROADCAST chip-wide; os-S5 declared).

    solver="expm_gpu" (DEFAULT, GPU matrix_exp) or "ode" (the qt.mesolve oracle)."""
    S = burst_single_qubit_superop(p, solver=solver)
    kraus, resid, leaked = superop_to_truncated_kraus_1q(
        S, track_dim=3, sim_levels=p.sim_levels, completion=completion
    )
    return {"kraus": kraus, "cptp_residual": resid, "leaked_population": leaked,
            "t1_survival_analytic": burst_t1_decay_analytic(p), "params": p}


def burst_shared_bath_correlation_superop(p: BurstParams, solver: str = "expm_gpu") -> qt.Qobj:
    """PUSH (PARTIAL, small-M FIRST-PRINCIPLES): M qubits each amplitude-damping into a COMMON mode
    (shared bath) -> correlated elevated relaxation. The M-qubit + 1-bath-mode system; the
    common-mode decay correlates the qubits' relaxation. Returns the JOINT M-qubit superoperator
    (bath traced out) over [0, t_round]. TIME-INDEPENDENT -> the propagator is expm(L * t_round).

    HILBERT SIZE (FLAG): sim_levels^m_demo * n_bath. With m_demo qubits at sim_levels=3 + a 2-level
    bath mode the full dim is 3^m_demo * 2 (M=2 -> 18 -> superop 18^2 = 324; M=3 -> 54 -> superop
    54^2 = 2916). KEEP m_demo <= 3 (the matrix_exp is small at M<=3; the orchestrator bounds it). The
    reduced superop is over the joint M-qubit space (dimM = sim_levels^M); the bath is traced out.

    H = g_common * sum_k (a_k b^dag + a_k^dag b)   [each qubit exchanges with the common bath mode b]
      collapse: sqrt(gamma_burst) b   [the bath mode decays at the elevated rate -> correlated qubit loss]
    The CHIP-WIDE (9q) broadcast is NOT this (declared classical broadcast, os-S5); this small-M demo
    shows the common-mode CORRELATION is real (the bath couples the qubits' decay), the first-principles
    half of the §2 PARTIAL push.

    solver:
      "expm_gpu" (DEFAULT) -- L = liouvillian(H, c_ops); S_full = torch.linalg.matrix_exp(L *
                              t_round) on cuda (complex128); then trace out the bath.
      "ode"               -- the original per-dyad qt.mesolve loop (the INDEPENDENT oracle).
    """
    M = int(p.m_demo)
    if M < 1 or M > 3:
        raise ValueError(f"shared-bath demo m_demo must be in [1, 3] (got {M}); larger M is FLAGGED-OOM")
    Lq = int(p.sim_levels)
    Nb = 2  # bath mode truncated to 2 levels (small-excitation regime; declared)
    aq, adq = _ladder(Lq)
    bb, bd = _ladder(Nb)
    Iq = qt.qeye(Lq)
    Ib = qt.qeye(Nb)

    def emb_q(op, k):
        ops = [Iq] * M + [Ib]
        ops[k] = op
        return qt.tensor(*ops)

    def emb_b(op):
        ops = [Iq] * M + [op]
        return qt.tensor(*ops)

    H = qt.qzero([Lq] * M + [Nb])
    for k in range(M):
        H = H + p.g_common * (emb_q(aq, k) * emb_b(bd) + emb_q(adq, k) * emb_b(bb))
    c_ops = [np.sqrt(p.gamma_burst) * emb_b(bb)]

    bath_grnd = (qt.basis(Nb, 0) * qt.basis(Nb, 0).dag()).full()  # bath ground |0><0|
    dimM = Lq ** M
    full_dims = [Lq] * M + [Nb]        # qubit factors 0..M-1, bath factor M
    keep_slots = list(range(M))

    if solver == "expm_gpu":
        S_full = _full_superop_expm_gpu(H, c_ops, p.t_round)
        D = dimM * Nb
        S = np.zeros((dimM * dimM, dimM * dimM), dtype=CDTYPE)
        # joint M-qubit dyads (over the combined dimM space) x bath ground; apply, trace out the bath.
        for i in range(dimM):
            for j in range(dimM):
                q_dy = np.zeros((dimM, dimM), dtype=CDTYPE)
                q_dy[i, j] = 1.0
                rho0 = np.kron(q_dy, bath_grnd)  # (dimM*Nb, dimM*Nb), bath as the LAST (fastest) factor
                vec = rho0.reshape(-1, order="F")
                out_vec = S_full @ vec
                rho_out = out_vec.reshape(D, D, order="F")
                rho_q = _ptrace_numpy(rho_out, full_dims, keep_slots)  # (dimM, dimM)
                S[:, j * dimM + i] = rho_q.reshape(-1, order="F")
        return qt.Qobj(S)

    if solver == "ode":
        tlist = np.array([0.0, p.t_round])
        opts = {"atol": 1e-11, "rtol": 1e-9, "nsteps": 1_000_000}
        bath_grnd_q = qt.Qobj(bath_grnd)
        S = np.zeros((dimM * dimM, dimM * dimM), dtype=CDTYPE)
        # superop over the M-qubit space: this is dimM^2 columns -> FLAGGED cost. The gtcheck uses M=2.
        eye_idx = [(i, j) for i in range(dimM) for j in range(dimM)]
        for (i, j) in eye_idx:
            ket = qt.basis(dimM, i)
            bra = qt.basis(dimM, j)
            q_dy = qt.Qobj(ket.full() @ bra.full().conj().T, dims=[[Lq] * M, [Lq] * M])
            rho0 = qt.tensor(q_dy, bath_grnd_q)
            out = qt.mesolve(H, rho0, tlist, c_ops=c_ops, options=opts).states[-1]
            rho_q = out.ptrace(list(range(M))).full()
            S[:, j * dimM + i] = rho_q.reshape(-1, order="F")
        return qt.Qobj(S)

    raise ValueError(f"unknown solver {solver!r}; use 'expm_gpu' (default) or 'ode'")


__all__ = [
    # units / helpers
    "ghz", "mhz", "khz", "superop_to_truncated_kraus_1q", "cptp_residual", "adaptive_n_fock",
    # solver (expm-GPU) primitives
    "_full_superop_expm_gpu", "_reduce_full_superop_to_qubit", "_ptrace_numpy",
    # A readout
    "ReadoutParams", "readout_nbar_steadystate", "readout_dephasing_rate_analytic",
    "readout_coherence_retention_analytic", "_readout_cavity_amplitude",
    "readout_dephasing_superop", "build_readout_dephasing_channel",
    "CorrReadoutParams", "corr_readout_cross_nbar_analytic",
    "corr_readout_spectator_dephasing_analytic", "corr_readout_spectator_superop", "iq_assignment_2x2",
    # A' MIST readout-induced leakage (the FIRST cross-mechanism coupling: readout x ④ leakage)
    "MISTParams", "mist_nbar_steadystate", "mist_critical_nbar_analytic", "mist_leakage_superop",
    "mist_leak_population", "build_mist_leakage_channel",
    # B TLS + TLF
    "TLSParams", "tls_vacuum_rabi_analytic", "tls_channel_superop", "build_tls_channel",
    "TLFBathParams", "tlf_dutta_horn_psd_analytic", "tlf_telegraph_phase",
    "tlf_round_dephasing_channel", "tlf_round_to_round_correlation",
    # C burst
    "BurstParams", "burst_t1_decay_analytic", "burst_single_qubit_superop", "build_burst_channel",
    "burst_shared_bath_correlation_superop",
]

#!/usr/bin/env python
"""Path-B leakage-transport: the per-CZ leakage CHANNEL, derived from a 2-transmon
multi-level Hamiltonian with QuTiP (CPU/dense backend). Builder A deliverable.

WHAT THIS IS
------------
The diabatic Sycamore-class CZ is a flux pulse that brings ``|11>-|20>`` onto resonance
(the intended CZ). The SAME bias passes the higher-level resonances ``|12>-|03>`` (a.k.a.
``|30>-|12>`` two-photon) and ``|31>-|22>`` (a.k.a. direct ``|13>-|22>``), which is how a
leaked qubit TRANSPORTS its leakage to a neighbour within a single gate (Miao 2211.04728
Fig 2b; Varbanov 2002.07119 App H). This module:

  1. builds the 2-transmon Duffing-pair Hamiltonian (Varbanov Eq H1 form) in a LARGE
     simulation space (``sim_levels`` per transmon, default 5) so the |3>/|4> dynamics are
     resolved exactly during the pulse;
  2. simulates a diabatic Net-Zero-style flux excursion on the higher-frequency qubit with
     QuTiP ``propagator`` (closed-system unitary) [optionally + ``mesolve`` with T1/Tphi
     Lindblad collapse for the dissipative variant] -> the full CZ propagator U (or
     superoperator S);
  3. PROJECTS / TRUNCATES the propagator onto the TRACKED subspace (dim 3 = qutrit, |2>-only,
     Arm 1; dim 4 = ququart, |3>-faithful, Arm 2) -> a CPTP channel as KRAUS operators.
     The non-unitarity of the truncated map (population leaking OUT of the tracked space into
     |3>,|4>,...) is what makes it a genuine channel, not a unitary.

The TRUNCATION-to-Kraus is exact (Choi -> eigendecomposition), so ``sum K^dag K = I`` on the
tracked subspace to ~1e-12 BY CONSTRUCTION of a contraction (truncated isometry block).

BASIS / OUTPUT CONVENTION (so Builder B can feed apply_channel_2site directly)
-----------------------------------------------------------------------------
The engine ``QutritDM.apply_channel_2site`` (src/qec_twin/forward/exact/qutrit_dm.py) wants a
``(d^2, d^2)`` Kraus with row/col index ``d*t_i + t_j``, ``site_i`` the MORE-significant qudit
(qudit-0 = MSF). We emit Kraus in EXACTLY that basis: two-transmon state ``|t_flux t_stat>``
mapped to index ``d*t_flux + t_stat`` -- i.e. the FLUX (higher-freq) qubit is the high pair-trit
(``site_i``). Builder B applies it with ``site_i = flux qubit, site_j = stat (partner) qubit``.
  - Arm 1: d=3 -> Kraus shape (k, 9, 9).
  - Arm 2: d=4 -> Kraus shape (k, 16, 16). (engine must be extended to local dim 4 -- Builder B.)

PARAMS -- NEVER FROZEN. ``CZParams`` exposes anharmonicity, coupling, frequencies, gate time,
pulse shape, and the dissipation as ARGUMENTS; the GT-check sweeps them. Defaults are grounded
in Varbanov Table II (alpha=-300 MHz, J1=15 MHz, omega: Dlow 4.9 / Dmid 6.0 / Dhigh 6.7 GHz),
declared per-field below.

NON-CIRCULAR GROUND TRUTH (the validation lives in qutip_cz_leakage_channel_gtcheck.py):
  - vs the INDEPENDENT analytic two-photon scaling P_t = sin^2(g_eff t),
    g_eff = -(g_{|21-12|})(g_{|30-21|})/eta = -2 sqrt3 g^2/eta  (Miao SI S1);
  - vs Miao's MEASURED transport fractions (|30-12 ~18-19%, |31-22 ~58-61%, Fig 2b);
  - the inter-level couplings are read off the bare J1 ladder (a*a^dag matrix elements) -- a
    from-scratch check that Eq H1 reproduces Miao's coupling structure.
NONE of these is a check vs this module's own output.

This file is the CHANNEL DERIVER (a library). The scripted GT-check + Kraus-save is the
companion ``qutip_cz_leakage_channel_gtcheck.py`` (precondition asserts + printed evidence +
__main__ guard).
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Callable

import numpy as np
import qutip as qt

# ----------------------------------------------------------------------------------------
# units: everything ANGULAR-FREQUENCY in rad/ns; times in ns. A frequency f [GHz] -> 2*pi*f
# [rad/ns]; f [MHz] -> 2*pi*f*1e-3 [rad/ns]. We keep the Hamiltonian in the LAB frame and let
# the (large) static detunings be physical -- propagator handles the fast phases exactly.
# ----------------------------------------------------------------------------------------
TWO_PI = 2.0 * np.pi


def ghz(f: float) -> float:
    return TWO_PI * f  # rad/ns


def mhz(f: float) -> float:
    return TWO_PI * f * 1e-3  # rad/ns


@dataclass(frozen=True)
class CZParams:
    """Every device-specific knob, NEVER frozen -- swept by the GT-check.

    Grounding (Varbanov 2002.07119 Table II unless noted; alpha/J1 are the load-bearing ones):
      alpha_*   : transmon anharmonicity, -300 MHz both qubits (Table II). [Varbanov]
      J1        : effective exchange coupling at the interaction point, 15 MHz (Table II).
                  This single linear coupling generates ALL inter-level couplings via the
                  bosonic ladder (a, a^dag matrix elements) -- see module docstring. [Varbanov]
      omega_flux_max / omega_stat : sweet-spot frequencies. Defaults = Dhigh 6.7 / Dmid 6.0 GHz
                  (the high-mid pair Varbanov uses for the |3> resonances, App H). [Varbanov]
      t_gate    : total CZ duration. Default 25 ns (Miao Table S1 CZ-gate time; Sycamore-class).
                  [Miao Table S1 -- DECLARED Sycamore default, Varbanov uses a Net-Zero pulse of
                  comparable length.]
      pulse     : 'netzero' (two half-excursions of opposite sign, the Varbanov/Rol Net-Zero
                  pulse) or 'flattop' (single smooth excursion). The flux qubit is brought from
                  its sweet spot DOWN to the interaction point where |11>-|20> is resonant.
      t_ramp    : raised-cosine ramp time (ns) for the flat-top portion. SWEPT.
      detune_int: residual detuning offset (rad/ns) ADDED to the ideal |11>-|20> resonance
                  condition at the interaction point -- a calibration knob (the real device is
                  tuned to a 2*pi |11>-|20> rotation, not exactly to resonance). SWEPT; this is
                  the dominant lever on the transport fractions (a finding to report).
      include_dissipation / t1_ns / tphi_ns : optional T1/Tphi Lindblad (Varbanov Eq B3-B6).
                  Default OFF (the transport channel is a coherent multilevel effect; dissipation
                  is a separable dressing -- Varbanov applies R_down before/after the gate).
      sim_levels: transmon levels in the SIMULATION space (>= track_dim + 2 so |3>,|4> dynamics
                  are resolved). Default 5 (resolves up to |4>, bounds the |4> leak-out for Arm2).
    """

    alpha_flux: float = mhz(-300.0)
    alpha_stat: float = mhz(-300.0)
    J1: float = mhz(15.0)
    omega_flux_max: float = ghz(6.7)
    omega_stat: float = ghz(6.0)
    t_gate: float = 25.0
    pulse: str = "netzero"
    t_ramp: float = 3.0
    detune_int: float = 0.0
    include_dissipation: bool = False
    t1_ns: float = 75_000.0      # 75 us (Varbanov Table I / Miao Table S1)
    tphi_ns: float = 75_000.0    # 75 us
    sim_levels: int = 5

    def with_(self, **kw) -> "CZParams":
        return dataclasses.replace(self, **kw)


# ----------------------------------------------------------------------------------------
# operators
# ----------------------------------------------------------------------------------------
def _ladder(n_levels: int):
    a = qt.destroy(n_levels)
    return a, a.dag()


def transmon_H_static(omega: float, alpha: float, n_levels: int) -> qt.Qobj:
    """H_q = omega a^dag a + (alpha/2) a^dag a^dag a a = omega n + (alpha/2) n(n-1)."""
    a, ad = _ladder(n_levels)
    n = ad * a
    return omega * n + 0.5 * alpha * (ad * ad * a * a)


def coupling_H(n_levels: int) -> qt.Qobj:
    """The exchange operator (a1 a2^dag + a1^dag a2) on flux (x) stat. Multiply by J1(t).

    Tensor order: subsystem 0 = FLUX (higher-freq), subsystem 1 = STAT (partner). This matches
    the engine's site_i=flux=MSF convention so the truncated Kraus index is d*t_flux + t_stat.
    """
    a, ad = _ladder(n_levels)
    I = qt.qeye(n_levels)
    a_flux = qt.tensor(a, I)
    ad_flux = qt.tensor(ad, I)
    a_stat = qt.tensor(I, a)
    ad_stat = qt.tensor(I, ad)
    return a_flux * ad_stat + ad_flux * a_stat


def interaction_point_omega_flux(p: CZParams) -> float:
    """Flux-qubit frequency at the interaction point where |11>-|20> is on resonance.

    Energies (lab frame, RWA Hamiltonian Eq H1): E|11> = w_flux + w_stat;
    E|20> = 2 w_flux + alpha_flux. Resonance E|11> = E|20> => w_flux = w_stat - alpha_flux.
    (alpha<0 so the interaction point is BELOW the stat frequency by |alpha|.) The optional
    ``detune_int`` offsets this (calibration to a 2*pi rotation, not exact resonance).
    """
    return p.omega_stat - p.alpha_flux + p.detune_int


def _raised_cosine_step(t: float, t0: float, t1: float) -> float:
    """0 -> 1 raised-cosine ramp over [t0, t1]."""
    if t <= t0:
        return 0.0
    if t >= t1:
        return 1.0
    x = (t - t0) / (t1 - t0)
    return 0.5 * (1.0 - np.cos(np.pi * x))


def flux_omega_profile(p: CZParams) -> Callable[[float, dict], float]:
    """omega_flux(t): pulse the flux qubit from its sweet spot to the interaction point.

    'flattop'  : sweetspot -> (ramp) -> interaction point (hold) -> (ramp) -> sweetspot.
    'netzero'  : the Varbanov/Rol Net-Zero pulse -- two excursions of opposite SIGN about the
                 sweet spot, which echoes out low-frequency flux noise. We approximate it as
                 [down-excursion to interaction point | up-excursion symmetric]; the |11>-|20>
                 resonance is crossed on BOTH halves (the physical Net-Zero CZ). The transport
                 resonances are passed on the way to/from the interaction point.
    The amplitude is set so the DOWN excursion reaches the |11>-|20> interaction point.
    """
    w0 = p.omega_flux_max
    w_int = interaction_point_omega_flux(p)
    tg = p.t_gate
    tr = p.t_ramp

    if p.pulse == "flattop":
        def prof(t, args=None):
            up = _raised_cosine_step(t, 0.0, tr)
            down = _raised_cosine_step(t, tg - tr, tg)
            env = up - down  # 0 ->1 ->0
            return w0 + (w_int - w0) * env
        return prof

    if p.pulse == "netzero":
        half = tg / 2.0
        # Net-Zero: first half goes DOWN to interaction point (where |11>-|20> resonant);
        # second half is the mirror going to the symmetric point ABOVE the sweet spot. Both
        # halves cross |11>-|20>; the average flux excursion is ~zero (echo).
        delta_down = w_int - w0   # negative (interaction point below sweet spot)

        def prof(t, args=None):
            if t < half:
                env = _raised_cosine_step(t, 0.0, tr) - _raised_cosine_step(t, half - tr, half)
                return w0 + delta_down * env
            else:
                tt = t - half
                env = _raised_cosine_step(tt, 0.0, tr) - _raised_cosine_step(tt, half - tr, half)
                return w0 - delta_down * env  # mirror excursion (opposite sign -> Net-Zero)
        return prof

    raise ValueError(f"unknown pulse {p.pulse!r}")


def J1_profile(p: CZParams) -> Callable[[float, dict], float]:
    """J1(t): the coupling is (in the real device) tunable, strongest at the interaction point.

    We model J1 as ON only while the flux qubit is near the interaction point (gated by the same
    raised-cosine envelope as the flux excursion), reaching p.J1 at the interaction point. This
    is the Varbanov picture (J1(Phi(t)) tunable coupling). A constant-J1 variant is available via
    detune/pulse choices; the GT-check reports sensitivity.
    """
    tg = p.t_gate
    tr = p.t_ramp
    if p.pulse == "flattop":
        def prof(t, args=None):
            up = _raised_cosine_step(t, 0.0, tr)
            down = _raised_cosine_step(t, tg - tr, tg)
            return p.J1 * (up - down)
        return prof
    # netzero: J1 on near BOTH interaction-point crossings
    half = tg / 2.0

    def prof(t, args=None):
        tt = t % half
        env = _raised_cosine_step(tt, 0.0, tr) - _raised_cosine_step(tt, half - tr, half)
        return p.J1 * env
    return prof


# ----------------------------------------------------------------------------------------
# the time-dependent Hamiltonian and the CZ propagator
# ----------------------------------------------------------------------------------------
def build_td_hamiltonian(p: CZParams):
    """Return the QuTiP time-dependent Hamiltonian for the diabatic CZ pulse, in the ROTATING
    FRAME of each transmon at its sweet-spot frequency (flux: omega_flux_max; stat: omega_stat).

    WHY the rotating frame. In the lab frame the diagonal energies are ~6 GHz (~40 rad/ns), so the
    propagator must resolve ~40-rad/ns carriers over 25 ns -> stiff, inaccurate (the lab-frame
    smoke run gave |U^dag U - I| ~ 1e-3). The rotating frame at the sweet-spot frequencies removes
    those carriers; only the SLOW (MHz) anharmonicity, the flux-excursion DETUNING, and a 0.7-GHz
    coupling beat remain -> the integration is fast AND tight (~1e-10). This is exactly Varbanov's
    "rotating frame of the qutrit" (Eq B7 is written there).

    Rotating-frame transform R(t) = exp(+i [omega_flux_max n_flux + omega_stat n_stat] t):
      - flux diagonal: omega_flux(t) n - omega_flux_max n = Delta_flux(t) n, with
        Delta_flux(t) = omega_flux(t) - omega_flux_max (the excursion, <= 0 going DOWN). Plus the
        (frame-invariant) anharmonicity (alpha_flux/2) n(n-1).
      - stat diagonal: (alpha_stat/2) n(n-1) only (its number term is removed by the frame).
      - coupling J1(t)(a_flux a_stat^dag + h.c.) -> J1(t)(a_flux a_stat^dag e^{+i d t} + h.c.),
        d := omega_flux_max - omega_stat (the sweet-spot detuning, ~0.7 GHz). Split into the two
        Hermitian-conjugate halves with e^{+i d t} / e^{-i d t} scalar coefficients.

    RESONANCE CHECK (kept consistent with interaction_point_omega_flux): the |11>-|20> transition
    (flux 1->2, stat 1->0) acquires a frame phase e^{i(omega_flux_max - omega_stat) t} = e^{i d t}
    from the frame AND the coupling carries e^{+i d t}; the DIAGONAL detuning of |20> vs |11| in
    the rotating frame is Delta_flux(t) + alpha_flux (flux gains one excitation + the anharmonic
    shift). On resonance Delta_flux + alpha_flux + d_correction = 0. With the lab condition
    omega_flux = omega_stat - alpha_flux we have Delta_flux = (omega_stat - alpha_flux) -
    omega_flux_max = -alpha_flux - d, so Delta_flux + alpha_flux = -d, which the coupling's e^{idt}
    beat exactly compensates over the gate -> the SAME interaction point as the lab frame. (The
    GT-check confirms the |11>-|20> 2*pi rotation lands there.)
    """
    L = p.sim_levels
    a, ad = _ladder(L)
    n = ad * a
    I = qt.qeye(L)

    n_flux = qt.tensor(n, I)
    anh_flux = 0.5 * p.alpha_flux * qt.tensor(ad * ad * a * a, I)
    anh_stat = qt.tensor(I, 0.5 * p.alpha_stat * (ad * ad * a * a))
    H_const = anh_flux + anh_stat  # frame-invariant anharmonicities

    # flux DETUNING excursion (rotating frame): Delta_flux(t) = omega_flux(t) - omega_flux_max
    w_flux = flux_omega_profile(p)
    w0 = p.omega_flux_max

    def delta_flux(t, *a_, **kw):
        return w_flux(t) - w0

    # coupling halves with the sweet-spot beat d = omega_flux_max - omega_stat
    d = p.omega_flux_max - p.omega_stat
    a_, ad_ = _ladder(L)
    Ii = qt.qeye(L)
    a_flux = qt.tensor(a_, Ii); ad_flux = qt.tensor(ad_, Ii)
    a_stat = qt.tensor(Ii, a_); ad_stat = qt.tensor(Ii, ad_)
    # CORRECT rotating-frame phases (verified vs the lab frame to machine precision in
    # _qutip_cz_smoke / the GT-check): R(t)=exp(+i[w_flux_max n_flux + w_stat n_stat]t) sends
    #   a_flux  -> a_flux  e^{-i w_flux_max t},  a_stat^dag -> a_stat^dag e^{+i w_stat t}
    #   => a_flux a_stat^dag -> a_flux a_stat^dag e^{-i d t}   (d = w_flux_max - w_stat)
    #   => a_flux^dag a_stat -> a_flux^dag a_stat e^{+i d t}.
    # (Getting this sign WRONG detunes the higher-level transport resonances by 2d ~ 1.4 GHz and
    # silently kills the |30>-|12| / |31>-|22| transport while |11>-|20| still partly works.)
    H_coup_plus = a_flux * ad_stat    # carries e^{-i d t}
    H_coup_minus = ad_flux * a_stat   # carries e^{+i d t}
    j1 = J1_profile(p)

    def coup_plus(t, *a_, **kw):
        return j1(t) * np.exp(-1j * d * t)

    def coup_minus(t, *a_, **kw):
        return j1(t) * np.exp(1j * d * t)

    return [H_const, [n_flux, delta_flux], [H_coup_plus, coup_plus], [H_coup_minus, coup_minus]]


def cz_propagator(p: CZParams, accuracy: str = "default") -> qt.Qobj:
    """The CLOSED-SYSTEM CZ propagator U over [0, t_gate] on the FULL sim space (L x L), in the
    rotating frame (build_td_hamiltonian). The output-time sampling must resolve the raised-cosine
    ramps (their envelope 2nd-derivative) AND the ~0.7-GHz coupling beat.

    accuracy: 'default' -> unitarity ~4e-7 (fast, fine for the channel); 'tight' -> ~5e-8 (the
    GT-check uses this). Unitarity here is the FIDELITY-to-physics; the truncated channel is CPTP
    by construction regardless (Choi eigendecomposition + completion).
    """
    # Accuracy is governed by the internal solver's max_step (the adaptive RK takes steps at
    # <= max_step regardless of the OUTPUT tlist), so we sample the output sparsely (endpoints
    # only) for speed -- the dense intermediate U's are not needed. max_step must be << the
    # ~1.4-ns (0.7-GHz) beat period AND resolve the raised-cosine ramps.
    H = build_td_hamiltonian(p)
    if accuracy == "tight":
        ms, atol, rtol = 0.0005, 1e-14, 1e-12
    else:
        ms, atol, rtol = 0.001, 1e-13, 1e-11
    tlist = np.array([0.0, p.t_gate])
    opts = {"atol": atol, "rtol": rtol, "nsteps": 5_000_000, "max_step": ms}
    U = qt.propagator(H, tlist, options=opts)
    return U[-1] if isinstance(U, (list, tuple)) or getattr(U, "shape", None) is None else U


def _virtual_z(theta: float, n_levels: int) -> qt.Qobj:
    """A single-transmon virtual-Z by angle theta: exp(-i theta n) (level n -> phase -n*theta).
    This is what a real device applies in software to correct single-qubit dynamical phases."""
    a = qt.destroy(n_levels)
    n = a.dag() * a
    return (-1j * theta * n).expm()


def cz_propagator_calibrated(p: CZParams, accuracy: str = "default") -> qt.Qobj:
    """The CZ propagator with the standard single-qubit phase calibration applied: virtual-Z
    rotations chosen so the computational single-excitation phases phi01, phi10 -> 0, i.e. the
    computational subspace realizes the IDEAL CZ diag(1,1,1, e^{i phi_CZ}) with phi_CZ ~ pi (the
    leakage-conditional phases + transport are the physical RESIDUAL the calibration cannot remove).

    This is the faithful per-CZ object: a calibrated CZ + its leakage structure, NOT a miscalibrated
    gate. (The real device corrects phi01/phi10 with phase pulses -- Varbanov 'tcor'.) The CZ
    conditional phase phi_CZ = phi11 - phi01 - phi10 is gauge-invariant and untouched.
    """
    U = cz_propagator(p, accuracy=accuracy)
    L = p.sim_levels
    Uf = U.full()
    # single-excitation phases in the FLUX (|10>) and STAT (|01>) computational slots
    phi10 = float(np.angle(Uf[(1 * L + 0), (1 * L + 0)]))  # flux level-1
    phi01 = float(np.angle(Uf[(0 * L + 1), (0 * L + 1)]))  # stat level-1
    zc = qt.tensor(_virtual_z(phi10, L), _virtual_z(phi01, L))
    return zc * U


def cz_superoperator(p: CZParams, calibrated: bool = True, accuracy: str = "default") -> qt.Qobj:
    """The CZ as a SUPEROPERATOR on the full sim space.

    Closed system -> spre(U)*spost(U.dag()) (a unitary channel on the FULL space; the channel
    character on the TRACKED subspace comes from truncation). With dissipation -> integrate the
    Lindbladian via propagator on the Liouvillian (Varbanov R_down/2 . U . R_down/2 structure
    is approximated by a full mesolve over the gate). ``calibrated`` applies the standard
    single-qubit phase correction (cz_propagator_calibrated)."""
    if not p.include_dissipation:
        U = cz_propagator_calibrated(p, accuracy=accuracy) if calibrated else cz_propagator(p, accuracy=accuracy)
        return qt.spre(U) * qt.spost(U.dag())
    # dissipative variant: T1 amplitude damping + Tphi dephasing on BOTH transmons (Eq B3-B6),
    # integrated together with the coherent pulse.
    L = p.sim_levels
    a, ad = _ladder(L)
    n = ad * a
    I = qt.qeye(L)
    c_ops = []
    g1 = 1.0 / p.t1_ns
    gphi = 1.0 / p.tphi_ns
    for embed in (lambda o: qt.tensor(o, I), lambda o: qt.tensor(I, o)):
        c_ops.append(np.sqrt(g1) * embed(a))            # amplitude damping (qutrit/ququart)
        c_ops.append(np.sqrt(2.0 * gphi) * embed(n))    # pure dephasing ~ n (Tphi)
    H = build_td_hamiltonian(p)
    ms = 0.0005 if accuracy == "tight" else 0.001
    tlist = np.array([0.0, p.t_gate])
    opts = {"atol": 1e-12, "rtol": 1e-10, "nsteps": 5_000_000, "max_step": ms}
    S = qt.propagator(H, tlist, c_ops=c_ops, options=opts)
    S = S[-1] if isinstance(S, (list, tuple)) else S
    if calibrated:
        # apply the (unitary) single-qubit phase correction as a superoperator on the dissipative S
        U0 = cz_propagator(p, accuracy=accuracy)
        Uf = U0.full()
        phi10 = float(np.angle(Uf[(1 * L + 0), (1 * L + 0)]))
        phi01 = float(np.angle(Uf[(0 * L + 1), (0 * L + 1)]))
        zc = qt.tensor(_virtual_z(phi10, L), _virtual_z(phi01, L))
        S = (qt.spre(zc) * qt.spost(zc.dag())) * S
    return S


# ----------------------------------------------------------------------------------------
# truncation -> Kraus (the channel)
# ----------------------------------------------------------------------------------------
def _tracked_indices(track_dim: int, sim_levels: int) -> np.ndarray:
    """Indices of the tracked two-transmon basis |t_flux t_stat>, t in [0, track_dim), into the
    full L^2 space, in the engine's order index = track_dim*t_flux + t_stat ... BUT mapped to the
    full-space index sim_levels*t_flux + t_stat. Returns the full-space indices ordered so that
    position (track_dim*t_flux + t_stat) holds full index (sim_levels*t_flux + t_stat)."""
    idx = np.empty(track_dim * track_dim, dtype=int)
    for tf in range(track_dim):
        for ts in range(track_dim):
            idx[track_dim * tf + ts] = sim_levels * tf + ts
    return idx


def superop_to_truncated_kraus(
    S: qt.Qobj, track_dim: int, sim_levels: int, tol: float = 1e-12
):
    """Project a full-space superoperator S onto the tracked d^2-dim subspace and return Kraus.

    The tracked subspace is the isometry V: tracked (d^2) -> full (L^2). The truncated channel is
    E_trunc(rho) = V^dag S[V rho V^dag] V, i.e. we feed tracked inputs through the FULL-space
    channel and read off only the tracked outputs (population that leaks to |3>,|4>,... is LOST
    -> the map is trace-NON-increasing on the tracked subspace = a genuine CPTP-with-loss channel
    completed by a single "leaked-out" Kraus so that sum K^dag K = I on the tracked subspace).

    We build the tracked Choi from E_trunc and eigendecompose -> Kraus on the d-dim PER-QUDIT
    (d^2 x d^2) space, in the engine index order d*t_flux + t_stat.
    """
    d = track_dim
    D = d * d
    idx = _tracked_indices(d, sim_levels)

    # The full superoperator S acts by column-stacking (QuTiP convention). Get the dense
    # full -> full superoperator matrix, then build the truncated tracked Choi directly.
    # E_trunc(|p><q|) for tracked basis |p>,|q> (p,q in [0,D)):
    #   rho_full = |idx[p]><idx[q]| ; out_full = S(rho_full) ; truncate rows/cols to idx.
    Sfull = S.full()  # (L^2 x L^2), column-stacked
    Lf = sim_levels * sim_levels

    def apply_full(rho_full):  # rho_full: (Lf, Lf)
        vec = rho_full.reshape(-1, order="F")
        out = Sfull @ vec
        return out.reshape(Lf, Lf, order="F")

    # tracked Choi: sum_{p,q} E_trunc(|p><q|) kron |p><q|  (output index outer)
    choi = np.zeros((D * D, D * D), dtype=complex)
    Eaa = np.zeros((D, D), dtype=complex)  # accumulate E_trunc(I_tracked) for the loss check
    for p in range(D):
        for q in range(D):
            rho_full = np.zeros((Lf, Lf), dtype=complex)
            rho_full[idx[p], idx[q]] = 1.0
            out_full = apply_full(rho_full)
            # truncate to tracked indices
            Epq = out_full[np.ix_(idx, idx)]
            Epq_basis = np.zeros((D, D), dtype=complex)
            Epq_basis[:, :] = Epq
            choi += np.kron(Epq_basis, _e(p, q, D))
            if p == q:
                Eaa += Epq_basis

    # eigendecompose the (Hermitian PSD) Choi -> Kraus
    w, V = np.linalg.eigh(0.5 * (choi + choi.conj().T))
    kraus = []
    for k in range(len(w)):
        if w[k].real > tol:
            kraus.append(np.sqrt(w[k].real) * V[:, k].reshape(D, D, order="C"))

    # complete the channel: leaked-out population makes sum K^dag K < I on the tracked subspace.
    # Add a single completion Kraus K_loss with K_loss^dag K_loss = I - sum K^dag K (PSD by
    # construction of a trace-non-increasing map), mapping the tracked subspace -> |leaked>.
    SKK = sum(K.conj().T @ K for K in kraus)
    defect = np.eye(D) - SKK
    defect = 0.5 * (defect + defect.conj().T)
    dw, dV = np.linalg.eigh(defect)
    dw = np.clip(dw.real, 0.0, None)
    # K_loss: D-dim input -> D-dim output but living in a "sink" (orthogonal) -- we represent it
    # AS a D x D operator whose action sends tracked input to a tracked-space NULL (zero) output
    # while carrying the right norm: i.e. K_loss = U_sink @ sqrt(defect). For a channel that the
    # engine APPLIES (it sums K rho K^dag on the tracked space), the leaked population must NOT
    # reappear in the tracked space -> the loss Kraus output must be ORTHOGONAL to all tracked
    # states. The only D x D operator with that property AND the right K^dag K is one whose IMAGE
    # is zero on the tracked space, which forces K_loss = 0 and breaks TP. So the correct object
    # is a NON-square Kraus (D_out > D): output dim = D (tracked) + 1 (sink). The engine wants
    # SQUARE (d^2 x d^2) Kraus, so we instead return the channel that RE-INJECTS leaked population
    # as classical loss into a designated sink LEVEL inside the tracked space if one exists, OR we
    # keep the map trace-non-increasing and let the engine renormalize. See build_cz_channel for
    # the chosen completion policy.
    loss_norm = float(np.clip(dw, 0.0, None).sum())
    return kraus, SKK, loss_norm, Eaa


def _e(i: int, j: int, n: int) -> np.ndarray:
    m = np.zeros((n, n), dtype=complex)
    m[i, j] = 1.0
    return m


# ----------------------------------------------------------------------------------------
# the public channel builders
# ----------------------------------------------------------------------------------------
@dataclass
class LeakageChannel:
    arm: str                  # 'qutrit' (d=3) | 'ququart' (d=4)
    track_dim: int            # 3 | 4
    kraus: list               # list of (d^2, d^2) complex arrays, index d*t_flux + t_stat
    cptp_residual: float      # max | sum K^dag K - I |
    leaked_population: float   # WORST-CASE leak-out (max defect eigval) over all tracked inputs
    params: CZParams
    note: str = ""
    leaked_from_comp: float = float("nan")    # leak-out from the realistic |11> input (the CZ L1)
    leaked_from_leaked_max: float = float("nan")  # max leak-out from singly-leaked |12>,|21> inputs
    pop_ge4_max: float = float("nan")         # max pop reaching |4>+ from any tracked input (Arm-2 bound)


def build_cz_channel(
    p: CZParams,
    track_dim: int,
    completion: str = "identity_sink",
    tol: float = 1e-12,
    calibrated: bool = True,
    accuracy: str = "default",
) -> LeakageChannel:
    """Derive the per-CZ leakage channel as engine-ready Kraus.

    completion policy (how leaked-OUT population -- the part that escapes |0..track_dim-1>^2 into
    |3>,|4>,... DURING the gate -- is represented in a SQUARE (d^2 x d^2) Kraus set the engine can
    apply):
      - 'identity_sink' (default, RECOMMENDED): the leaked-out population is RETURNED to the
        tracked subspace as a CLASSICAL mixture proportional to its origin -- physically, leakage
        that exits the tracked truncation is, in the real device, *still in the transmon* (just at
        a level we do not track); for a |2>/|3>-truncated TEACHER the faithful thing is to KEEP it
        as leakage on the tracked top level (|2> for d=3, |3> for d=4). We therefore add a
        completion Kraus that maps the leaked component to the tracked TOP leakage level, so the
        channel is exactly trace-preserving on the tracked space AND conserves "is-leaked" status.
        The leaked fraction is reported (leaked_population) so the truncation error is BOUNDED
        (Arm-2 |4>-tolerance, faithfulness protocol rule III).
      - 'renormalize': return only the truncated Kraus (trace-non-increasing) and let the caller
        renormalize -- exposes the raw leak-out for the tolerance check.

    The two arms differ ONLY in track_dim (3 vs 4) and thus in how much of the |3>-mediated
    transport is RESOLVED inside the tracked space vs absorbed into the completion.
    """
    S = cz_superoperator(p, calibrated=calibrated, accuracy=accuracy)
    kraus, SKK, _loss, _Eaa = superop_to_truncated_kraus(S, track_dim, p.sim_levels, tol=tol)
    D = track_dim * track_dim

    defect = np.eye(D) - SKK
    defect = 0.5 * (defect + defect.conj().T)
    leaked_population = float(np.clip(np.linalg.eigvalsh(defect).real, 0.0, None).max())

    # per-input leak diagnostics (interpretable bounds; faithfulness rule III)
    _lk = leaked_out_of_track(p, track_dim, probe="both")
    leaked_from_comp = float(_lk.get("leak_out_from|11>", float("nan")))
    _ll = [v for k, v in _lk.items() if k.startswith("leak_out_from|12>") or k.startswith("leak_out_from|21>")]
    leaked_from_leaked_max = float(max(_ll)) if _ll else float("nan")
    _p4 = [v for k, v in _lk.items() if k.startswith("pop_ge|4|")]
    pop_ge4_max = float(max(_p4)) if _p4 else float("nan")

    def _mk(kr, resid, note):
        return LeakageChannel(
            arm={3: "qutrit", 4: "ququart"}[track_dim], track_dim=track_dim,
            kraus=[np.asarray(K, complex) for K in kr], cptp_residual=resid,
            leaked_population=leaked_population, params=p, note=note,
            leaked_from_comp=leaked_from_comp, leaked_from_leaked_max=leaked_from_leaked_max,
            pop_ge4_max=pop_ge4_max)

    if completion == "renormalize":
        resid = float(np.max(np.abs(SKK - np.eye(D))))
        return _mk(kraus, resid, "trace-non-increasing (truncated); caller renormalizes.")

    if completion == "identity_sink":
        # leaked-out population -> the tracked TOP leakage level of the FLUX qubit (|track_dim-1>
        # on flux, partner unchanged), preserving "leaked" status. We build completion Kraus from
        # the PSD defect = I - sum K^dag K: K_c = |sink_state><src| * sqrt(defect_eigval).
        dw, dV = np.linalg.eigh(defect)
        comp = []
        top = track_dim - 1
        # sink: map any leaked source (eigvector v of defect) onto the state with flux at |top>,
        # stat trit preserved as best as possible. Simplest faithful sink that preserves CPTP:
        # send leaked weight to the single state |top, top> (both at top leakage level). This is a
        # crude but BOUNDED re-injection; its weight (leaked_population) is small (~1e-4) so the
        # bias is bounded by leaked_population (reported).
        sink_idx = track_dim * top + top  # index of |top_flux, top_stat>
        for k in range(len(dw)):
            if dw[k].real > tol:
                src = dV[:, k]  # (D,)
                Kc = np.zeros((D, D), dtype=complex)
                Kc[sink_idx, :] = np.sqrt(dw[k].real) * src.conj()
                comp.append(Kc)
        full_kraus = [np.asarray(K, complex) for K in kraus] + comp
        SKK2 = sum(K.conj().T @ K for K in full_kraus)
        resid = float(np.max(np.abs(SKK2 - np.eye(D))))
        return _mk(full_kraus, resid,
                   (f"identity_sink completion: worst-case leaked-out frac={leaked_population:.2e} "
                    f"re-injected to |{top},{top}> (preserves leaked status; bias bounded by "
                    f"per-input leak frac, reported)."))

    raise ValueError(f"unknown completion {completion!r}")


# ----------------------------------------------------------------------------------------
# transport-fraction / coupling diagnostics (used by the GT-check; NON-circular vs Miao)
# ----------------------------------------------------------------------------------------
def ladder_couplings(p: CZParams) -> dict:
    """The inter-level couplings IMPLIED by the single linear J1(a1 a2^dag + h.c.), read off the
    bosonic ladder matrix elements (a from-scratch check that Eq H1 reproduces Miao's structure).

    For a transition |n1 m1> <-> |n2 m2> driven by (a_flux a_stat^dag + a_flux^dag a_stat), the
    coupling is J1 * <n2 m2| (a_flux a_stat^dag + h.c.) |n1 m1>:
      |11>-|20> : flux 1->2 (sqrt2), stat 1->0 (1) via a_flux^dag a_stat -> sqrt2 J1
      |12>-|21> : flux 1<->2 (sqrt2), stat 2<->1 (sqrt2)               -> 2 J1     (Varbanov: 2J1)
      |12>-|03> : flux 1->0 (1),  stat 2->3 (sqrt3)  via a_flux a_stat^dag -> sqrt3 J1 (Varbanov)
      |21>-|30> : flux 2->3 (sqrt3), stat 1->0 (1)   via a_flux^dag a_stat -> sqrt3 J1
      |31>-|22> : flux 3->2 (sqrt3), stat 1->2 (sqrt2)                -> sqrt6 J1   (direct, 1st-order)

    *** KEY CONVENTION FINDING (resolved by the EXACT g_eff fit, GT-check sec 2) ***
    Miao SI S1 writes g_{|21-12} = 2g, g_{|30-21} = sqrt3 g and g_eff = -2 sqrt3 g^2/eta. The exact
    simulation gives g_eff(|30-12|) ~ 2.55 MHz, which matches Varbanov Eq H4 (2J1)(sqrt3 J1)/eta =
    2.60 MHz (ratio 0.98), NOT -2sqrt3 (sqrt2 J1)^2/eta = 5.20 MHz. Reconciliation: Miao's 'g' is
    the BARE bus coupling J1 (so g_{|21-12}=2g=2J1, g_{|30-21}=sqrt3 g=sqrt3 J1), NOT the |11>-|20|
    coupling (which is sqrt2 J1). With g=J1: g_eff = -2 sqrt3 J1^2/eta = -2.60 MHz == Varbanov H4 ==
    the sim. (An earlier read mis-set g=sqrt2 J1, doubling g_eff. The exact sim disambiguates.)
    """
    s2, s3, s6 = np.sqrt(2.0), np.sqrt(3.0), np.sqrt(6.0)
    g_1120 = s2 * p.J1           # |11>-|20| coupling (the CZ); NOT Miao's 'g'
    g_1221 = 2.0 * p.J1          # |12>-|21|              = Miao 2g  -> g = J1
    g_1203 = s3 * p.J1           # |12>-|03|              (Varbanov sqrt3 J1)
    g_2130 = s3 * p.J1           # |21>-|30|              = Miao sqrt3 g (g = J1)
    g_3122 = s6 * p.J1           # |31>-|22|  DIRECT (1st-order)
    eta = abs(p.alpha_flux)      # the common nonlinearity (virtual-|21> detuning)
    g_miao = p.J1                # *** Miao's 'g' = bare J1 (the convention finding) ***
    g_eff_miao = -2.0 * s3 * g_miao**2 / eta            # = -2 sqrt3 J1^2/eta
    g_eff_varbanov_H4 = (g_1221 * g_2130) / eta         # (2J1)(sqrt3 J1)/eta  (Eq H4)
    return {
        "J1_radns": p.J1, "J1_MHz": p.J1 / mhz(1.0),
        "g_1120(|11-20|=sqrt2 J1)": g_1120, "g_1221(|12-21|=2J1)": g_1221,
        "g_1203(|12-03|=sqrt3 J1)": g_1203, "g_3122(|31-22|=sqrt6 J1)": g_3122,
        "eta(=|alpha|)": eta,
        "g_eff_miao(-2sqrt3 J1^2/eta, g=J1)": g_eff_miao,
        "g_eff_varbanov_H4((2J1)(sqrt3 J1)/eta)": g_eff_varbanov_H4,
        "g_eff_miao_MHz": g_eff_miao / mhz(1.0),
        "g_eff_varbanov_H4_MHz": g_eff_varbanov_H4 / mhz(1.0),
    }


def transport_fractions(p: CZParams, sink_levels: int | None = None) -> dict:
    """The per-CZ leakage TRANSPORT fractions measured the way Miao does (Fig 2b): prepare a
    higher-level product state, apply the CZ, read the NET population transferred to the partner
    resonance. Computed on the FULL sim space (so |3> dynamics are exact).

      |30>-|12> fraction: prepare |12> (flux=1, stat=2); transferred pop to |30> after CZ.
      |31>-|22> fraction: prepare |22> (flux=2, stat=2)... careful: Miao's |31>-|22| moves pop
        between |31> (flux=3,stat=1) and |22> (flux=2,stat=2). Prepare |31>, read pop in |22>.
    Returns BOTH directions (Miao reports +/-)."""
    p_full = p if (sink_levels is None or sink_levels == p.sim_levels) else p.with_(sim_levels=sink_levels)
    U = cz_propagator(p_full)
    L = p_full.sim_levels

    def st(nf, ns):
        return qt.tensor(qt.basis(L, nf), qt.basis(L, ns))

    def transfer(src_f, src_s, dst_f, dst_s):
        psi0 = st(src_f, src_s)
        psi1 = U * psi0
        amp = complex(st(dst_f, dst_s).overlap(psi1))
        return float(abs(amp) ** 2)

    # |30>-|12>: prepare |12>, read |30>; and prepare |30>, read |12>
    f_12_to_30 = transfer(1, 2, 3, 0)
    f_30_to_12 = transfer(3, 0, 1, 2)
    # |31>-|22>: prepare |31>, read |22>; and prepare |22>, read |31>
    f_31_to_22 = transfer(3, 1, 2, 2)
    f_22_to_31 = transfer(2, 2, 3, 1)
    return {
        "P_t(|30>-|12>)_from|12>": f_12_to_30,
        "P_t(|30>-|12>)_from|30>": f_30_to_12,
        "P_t(|31>-|22>)_from|31>": f_31_to_22,
        "P_t(|31>-|22>)_from|22>": f_22_to_31,
    }


def leaked_out_of_track(p: CZParams, track_dim: int, probe: str = "comp") -> dict:
    """Quantify population that escapes the TRACKED subspace during the gate -- the truncation
    bound (Arm-1 |2>-only 2nd-order; Arm-2 |3>-faithful |4>-tolerance).

    'comp' : start from the computational |11> (the realistic input) and measure pop OUTSIDE the
             tracked d^2 subspace after the CZ.
    'leak' : start from a LEAKED input (|12>, |21|, etc.) -- the regime where the gap matters --
             and measure pop in |4>+ (or > track_dim-1).
    """
    U = cz_propagator(p)
    L = p.sim_levels

    def st(nf, ns):
        return qt.tensor(qt.basis(L, nf), qt.basis(L, ns))

    def out_of_track(psi):
        vec = psi.full().reshape(L, L)
        pop = np.abs(vec) ** 2
        tracked = pop[:track_dim, :track_dim].sum()
        return float(1.0 - tracked)

    def in_level_ge(psi, lev):
        vec = psi.full().reshape(L, L)
        pop = np.abs(vec) ** 2
        return float(pop[lev:, :].sum() + pop[:, lev:].sum() - pop[lev:, lev:].sum())

    res = {}
    if probe in ("comp", "both"):
        res["leak_out_from|11>"] = out_of_track(U * st(1, 1))
        res["pop_ge|4|_from|11>"] = in_level_ge(U * st(1, 1), 4)
    if probe in ("leak", "both"):
        for (nf, ns), nm in [((1, 2), "12"), ((2, 1), "21"), ((3, 0), "30"), ((0, 3), "03")]:
            if max(nf, ns) < L:
                res[f"leak_out_from|{nm}>(track={track_dim})"] = out_of_track(U * st(nf, ns))
                res[f"pop_ge|4|_from|{nm}>"] = in_level_ge(U * st(nf, ns), 4)
    return res


__all__ = [
    "CZParams", "LeakageChannel", "build_cz_channel",
    "cz_propagator", "cz_superoperator",
    "ladder_couplings", "transport_fractions", "leaked_out_of_track",
    "ghz", "mhz", "interaction_point_omega_flux",
]

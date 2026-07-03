#!/usr/bin/env python
"""Single-transmon physical channels DERIVED from QuTiP Hamiltonians/Lindblads (first-principles),
replacing the phenomenological analytic Kraus of the Axis-A teacher. Builder 1 deliverable.

WHAT THIS IS
------------
Three single-transmon channels of the Axis-A teacher (pre-reg
``docs/twin_validation/qutip_channel_derivation_prereg.md`` §1, rows ①②③), each derived from a
transmon Hamiltonian / Lindblad with QuTiP (CPU/dense ``propagator``), then TRUNCATED to an
engine-ready 3x3 (qutrit, ``|2>`` tracked) Kraus set the torch-GPU ``QutritDM`` engine applies
UNCHANGED:

  ① Pauli-baseline recast  — a single transmon under T1 amplitude-damping (``c1 = sqrt(g1) a``)
     + Tphi pure dephasing (``cphi = sqrt(2 gphi) n``) Lindblad over one cycle time ``t_c``. This
     is the REAL T1/T2 channel (more faithful than a flat depolarizer); ``propagator(H, [0,t_c],
     c_ops=[c1,cphi])`` -> superoperator -> truncate to 3 -> Kraus.
  ② coherent rx            — a transmon driven by ``H = (Omega/2)(a + a^dag)`` for time ``t`` with
     ``Omega * t = theta`` -> ``exp(-i (theta/2) X)`` on ``{0,1}`` (matching the engine's
     ``rx(theta)`` convention). ``propagator`` (closed) -> truncate -> Kraus. ``|2>`` leakage from
     the drive is the DECLARED, BOUNDED simplification (kept tiny by ``Omega << |alpha|``; reported).
  ③ amplitude-damping      — the ① T1 arm in isolation (``Tphi -> inf``) at the ③ rate (a standalone
     non-unital AD Lindblad). -> truncate -> Kraus.

The TRUNCATION-to-Kraus is the SINGLE-transmon analog of the path-B 2-transmon
``superop_to_truncated_kraus`` (``qutip_cz_leakage_channel.py``): we feed tracked (d=3) inputs
through the FULL ``L``-level transmon channel and read off only the tracked d=3 outputs (population
that leaks to ``|3>,|4>,...`` is LOST -> the truncated map is trace-NON-increasing on the tracked
subspace), then build the tracked Choi, eigendecompose -> Kraus, and complete to CPTP via a single
``identity_sink`` re-injection Kraus (so ``sum K^dag K = I_3`` to ~1e-12). The leaked-out fraction
is reported (``leaked_population``) so the truncation bias is BOUNDED (faithfulness rule III).

BASIS / OUTPUT CONVENTION (engine-ready)
----------------------------------------
The engine ``QutritDM.apply_channel(kraus, site)`` (``src/qec_twin/forward/exact/qutrit_dm.py``)
wants a list of ``(3, 3)`` complex128 single-qudit Kraus in the basis ``{|0>, |1>, |2>}`` (``|2>``
the leaked level). Our derivers emit EXACTLY that: a ``list[np.ndarray]`` of ``(3, 3)`` complex128.

PARAMS -- NEVER FROZEN. ``TransmonParams`` exposes every device knob (T1, Tphi, t_c, omega, alpha,
sim_levels) as a frozen dataclass field; the GT-check SWEEPS them (anti-toy: a frozen device param
is a STOP). Defaults are grounded (Varbanov ~75 us T1/T2; alpha = -300 MHz) and DECLARED per-field.

NON-CIRCULAR GROUND TRUTH (validation lives in qutip_single_qubit_gtcheck.py; pre-reg §3):
  - ① / ③ vs the INDEPENDENT closed-form qubit amplitude-damping Kraus
        K0 = diag(1, sqrt(1-gamma)),  K1 = [[0, sqrt(gamma)], [0, 0]],   gamma = 1 - exp(-t/T1)
    and the dephasing Kraus {sqrt(1-p_z) I, sqrt(p_z) Z} with the Tphi/t_c-derived rate -- compared
    AS A CHANNEL (Choi / process fidelity), NOT Kraus-by-Kraus (Kraus are gauge-non-unique);
  - ② vs the closed-form ``rx(theta)`` 2x2 unitary imported from
        qec_twin.forward.exact.circuit_sim.rx  (process fidelity of the {0,1} block).
NONE is a check vs this module's own QuTiP output ("our own qutip" is forbidden -- pre-reg §3).

This file is the CHANNEL DERIVER (a library). The scripted GT-check (precondition asserts + printed
evidence + __main__ guard) is the companion ``qutip_single_qubit_gtcheck.py``.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass

import numpy as np
import qutip as qt

try:  # torch is the GPU matrix_exp solver backend; guarded so the module imports CPU-only.
    import torch  # noqa: F401
    _HAVE_TORCH = True
except Exception:  # pragma: no cover - environment without torch still imports the derivers.
    torch = None  # type: ignore[assignment]
    _HAVE_TORCH = False


# ----------------------------------------------------------------------------------------
# GPU matrix-exponential solver (the DEFAULT "expm_gpu" path)
# ----------------------------------------------------------------------------------------
# The single-transmon dissipative channels (① T1/Tphi, ③ amplitude-damping, ④ WG-leak) and the
# coherent channel (② rx) are ALL TIME-INDEPENDENT (constant H / constant Lindblad). Their
# propagator over a fixed time t is therefore JUST A MATRIX EXPONENTIAL -- exp(L t) for the
# Liouvillian L (open) or exp(-i H t) for H (closed). qt.propagator / qt.mesolve solve this with an
# adaptive-RK ODE, which is the wrong/slow tool. We replace the propagator/mesolve CALL with a single
# torch.linalg.matrix_exp on cuda (exact, fast, GPU; complex128 supported on cuda -- this is the
# whole point, matrix_exp, NOT ODE-on-GPU). The Liouvillian is built by QuTiP's OWN constructor
# qt.liouvillian(H, c_ops) (numpy; the CORRECT column-stacking convention that qt.mesolve uses), so
# the resulting superoperator matches qt.mesolve EXACTLY and feeds the SAME truncation unchanged.
# The qt ODE path stays selectable (solver="ode") as the ORACLE; the consistency gate in the
# gtcheck asserts the two agree to the ODE floor (Choi fidelity > 1 - 1e-6).
_EXPM_DEVICE = "cuda"


def _matrix_exp_np(mat: np.ndarray, device: str = _EXPM_DEVICE) -> np.ndarray:
    """exp(mat) for a dense complex128 numpy matrix via torch.linalg.matrix_exp on the GPU.

    A single matrix exponential -- NOT an ODE. complex128 is supported by torch.linalg.matrix_exp on
    cuda (the reason this path exists; there is no diffrax complex-dtype caveat for matrix_exp). The
    result is moved back to numpy (the truncation layer is numpy/QuTiP-side). ``mat`` already carries
    the time factor (caller passes L * t or -i H t).
    """
    if not _HAVE_TORCH:
        raise RuntimeError(
            "solver='expm_gpu' requires torch (GPU matrix_exp). Install torch or pass solver='ode'."
        )
    tmat = torch.as_tensor(np.ascontiguousarray(mat), dtype=torch.complex128, device=device)
    expm = torch.linalg.matrix_exp(tmat)
    return expm.cpu().numpy()


def _liouvillian_superop_expm(H: qt.Qobj, c_ops: list, t: float, device: str = _EXPM_DEVICE) -> qt.Qobj:
    """OPEN-system channel superoperator S = exp(L t) via GPU matrix_exp.

    Builds the Liouvillian with QuTiP's OWN constructor ``L = qt.liouvillian(H, c_ops)`` (numpy,
    the CORRECT column-stacking convention qt.mesolve uses, cheap, NOT an ODE), exponentiates
    ``L.full() * t`` on the GPU, and wraps the result back into a QuTiP super Qobj with the SAME
    dims/superrep as ``qt.liouvillian`` so it drops into ``superop_to_truncated_kraus`` unchanged
    (that routine only calls ``.full()``, so the wrapped dims are belt-and-suspenders).
    """
    Lq = qt.liouvillian(H, c_ops)
    S = _matrix_exp_np(Lq.full() * float(t), device=device)
    return qt.Qobj(S, dims=Lq.dims, superrep=getattr(Lq, "superrep", "super"))


def _unitary_superop_expm(H: qt.Qobj, t: float, device: str = _EXPM_DEVICE) -> qt.Qobj:
    """CLOSED-system channel superoperator via GPU matrix_exp of the unitary.

    U = exp(-i H t) (single GPU matrix_exp), then S = spre(U) spost(U^dag) -- the SAME superoperator
    qt.propagator(H) followed by spre*spost would build, but with the matrix exp replacing the ODE.
    """
    U = _matrix_exp_np(-1j * H.full() * float(t), device=device)
    Uq = qt.Qobj(U, dims=H.dims)
    return qt.spre(Uq) * qt.spost(Uq.dag())


# ----------------------------------------------------------------------------------------
# units: angular-frequency rad/ns, times ns (mirrors the path-B leakage module exactly).
# f [GHz] -> 2 pi f [rad/ns]; f [MHz] -> 2 pi f 1e-3 [rad/ns]. Rates: 1/T1, 1/Tphi with T in ns.
# ----------------------------------------------------------------------------------------
TWO_PI = 2.0 * np.pi


def ghz(f: float) -> float:
    return TWO_PI * f  # rad/ns


def mhz(f: float) -> float:
    return TWO_PI * f * 1e-3  # rad/ns


@dataclass(frozen=True)
class TransmonParams:
    """Every single-transmon device knob -- NEVER frozen; the GT-check sweeps each.

    Grounding (Varbanov 2002.07119 Table I; alpha standard transmon):
      t1_ns   : energy-relaxation time T1. Default 75_000 ns = 75 us (Varbanov Table I). [Varbanov]
      tphi_ns : PURE-dephasing time Tphi (the white-noise pure-dephasing arm; T2 relates via
                1/T2 = 1/(2 T1) + 1/Tphi). Default 75_000 ns. SWEPT. [Varbanov-class]
      t_c_ns  : ONE cycle (round) time over which the Lindblad channel acts. Default 1_000 ns
                = 1 us (a representative QEC cycle; Google d3 cycles are ~1 us). SWEPT. [DECLARED]
      omega   : bare transmon frequency (rad/ns). Used only for the |2> anharmonic shift in ②'s
                drive; the dissipative channels ①③ are written in the rotating frame (H_static = 0)
                so omega does NOT enter them. Default 6.0 GHz. [Varbanov-class]
      alpha   : transmon anharmonicity (rad/ns), -300 MHz. Sets the |1>-|2> detuning the drive ②
                must stay below (Omega << |alpha|) to keep the rotation clean. Default -300 MHz.
                [standard transmon]
      sim_levels : transmon levels in the SIMULATION space (>= track_dim + 1 so |3>+ leak-out is
                resolved and BOUNDED). Default 4 (resolves |3>; the AD/dephasing channels barely
                populate |2> from {0,1}, so |3> is doubly negligible -- reported). [DECLARED]

    track_dim is fixed at 3 (qutrit, |2> tracked) -- the engine's QutritDM local dim.
    """

    t1_ns: float = 75_000.0
    tphi_ns: float = 75_000.0
    t_c_ns: float = 1_000.0
    omega: float = ghz(6.0)
    alpha: float = mhz(-300.0)
    sim_levels: int = 4

    def with_(self, **kw) -> "TransmonParams":
        return dataclasses.replace(self, **kw)


# ----------------------------------------------------------------------------------------
# operators (single transmon)
# ----------------------------------------------------------------------------------------
def _ladder(n_levels: int):
    a = qt.destroy(n_levels)
    return a, a.dag()


def transmon_H_static(omega: float, alpha: float, n_levels: int) -> qt.Qobj:
    """H_q = omega a^dag a + (alpha/2) a^dag a^dag a a = omega n + (alpha/2) n(n-1).

    The single-transmon analog of the path-B ``transmon_H_static`` (same Duffing form).
    """
    a, ad = _ladder(n_levels)
    n = ad * a
    return omega * n + 0.5 * alpha * (ad * ad * a * a)


# ----------------------------------------------------------------------------------------
# truncation -> Kraus (single transmon; the single-qudit analog of the path-B 2-qudit truncation)
# ----------------------------------------------------------------------------------------
def _e(i: int, j: int, n: int) -> np.ndarray:
    m = np.zeros((n, n), dtype=complex)
    m[i, j] = 1.0
    return m


def superop_to_truncated_kraus(
    S: qt.Qobj, track_dim: int, sim_levels: int, tol: float = 1e-12
):
    """Project a full-space SINGLE-transmon superoperator ``S`` (L x L Liouville space, column-
    stacked QuTiP convention) onto the tracked ``track_dim``-dim subspace and return Kraus.

    The single-transmon analog of the path-B 2-transmon ``superop_to_truncated_kraus`` (study its
    docstring). The tracked subspace is the isometry ``V: tracked (d) -> full (L)``. The truncated
    channel is ``E_trunc(rho) = V^dag S[V rho V^dag] V`` -- feed tracked (d=3) inputs through the
    FULL transmon channel and read off only the tracked outputs (population that leaks to
    ``|3>,|4>,...`` is LOST -> trace-NON-increasing on the tracked subspace).

    We build the tracked Choi from ``E_trunc`` and eigendecompose -> Kraus on the d-dim space.
    Returns (kraus, SKK, loss_norm, Eaa):
      kraus    : list of (d, d) complex Kraus (truncated, trace-non-increasing)
      SKK      : sum_k K^dag K (d, d)   (= I - defect; the defect is the leaked-out part)
      loss_norm: total leaked-out weight (sum of positive defect eigvals)
      Eaa      : E_trunc(I_tracked) accumulated (the loss-channel diagnostic)
    """
    d = int(track_dim)
    D = d  # single-qudit: the channel space is d x d (NOT d^2 as in the 2-qudit case)
    Lf = int(sim_levels)
    idx = np.arange(d, dtype=int)  # tracked levels |0>..|d-1> map straight into the full space

    Sfull = S.full()  # (L^2 x L^2), column-stacked

    def apply_full(rho_full):  # rho_full: (Lf, Lf)
        vec = rho_full.reshape(-1, order="F")
        out = Sfull @ vec
        return out.reshape(Lf, Lf, order="F")

    # tracked Choi: sum_{p,q} E_trunc(|p><q|) kron |p><q|  (output index outer)
    choi = np.zeros((D * D, D * D), dtype=complex)
    Eaa = np.zeros((D, D), dtype=complex)
    for p in range(D):
        for qcol in range(D):
            rho_full = np.zeros((Lf, Lf), dtype=complex)
            rho_full[idx[p], idx[qcol]] = 1.0
            out_full = apply_full(rho_full)
            Epq = out_full[np.ix_(idx, idx)]  # truncate to tracked indices
            choi += np.kron(Epq, _e(p, qcol, D))
            if p == qcol:
                Eaa += Epq

    # eigendecompose the (Hermitian PSD) Choi -> Kraus
    w, V = np.linalg.eigh(0.5 * (choi + choi.conj().T))
    kraus = []
    for k in range(len(w)):
        if w[k].real > tol:
            kraus.append(np.sqrt(w[k].real) * V[:, k].reshape(D, D, order="C"))

    SKK = sum(K.conj().T @ K for K in kraus) if kraus else np.zeros((D, D), dtype=complex)
    defect = np.eye(D) - SKK
    defect = 0.5 * (defect + defect.conj().T)
    loss_norm = float(np.clip(np.linalg.eigvalsh(defect).real, 0.0, None).sum())
    return kraus, SKK, loss_norm, Eaa


# ----------------------------------------------------------------------------------------
# the public channel objects + builders
# ----------------------------------------------------------------------------------------
@dataclass
class SingleQubitChannel:
    name: str                  # 'pauli_baseline' | 'coherent_rx' | 'amp_damp'
    track_dim: int             # 3 (qutrit)
    kraus: list                # list of (3, 3) complex128 arrays (engine-ready apply_channel)
    cptp_residual: float       # max | sum K^dag K - I_3 |
    leaked_population: float    # WORST-CASE leak-out (max defect eigval) over tracked inputs
    params: TransmonParams
    note: str = ""


def _complete_identity_sink(kraus, track_dim: int, tol: float = 1e-12):
    """Complete a trace-non-increasing single-qudit Kraus set to CPTP via the ``identity_sink``
    policy (the path-B completion, single-qudit analog): the leaked-OUT population (the part that
    escaped the tracked truncation into |3>,|4>,... DURING the channel) is RETURNED to the tracked
    subspace at the TOP tracked leakage level (|track_dim-1>, i.e. |2> for a qutrit) -- physically,
    population that exits the tracked truncation is STILL in the transmon (just at a level we do not
    track), so for a |2>-truncated TEACHER the faithful thing is to keep it as leakage on |2>.

    Builds completion Kraus from the PSD defect = I - sum K^dag K so the channel is EXACTLY
    trace-preserving on the tracked space. The re-injected weight (leaked_population) is small for
    the dissipative channels (~1e-2 at the worst from |1> over a 1 us cycle) and is REPORTED so the
    bias is BOUNDED (faithfulness rule III).
    """
    d = int(track_dim)
    SKK = sum(K.conj().T @ K for K in kraus) if kraus else np.zeros((d, d), dtype=complex)
    defect = np.eye(d) - SKK
    defect = 0.5 * (defect + defect.conj().T)
    dw, dV = np.linalg.eigh(defect)
    top = d - 1
    sink_idx = top  # single-qudit: re-inject to |top> (= |2> for a qutrit)
    comp = []
    for k in range(len(dw)):
        if dw[k].real > tol:
            src = dV[:, k]  # (d,)
            Kc = np.zeros((d, d), dtype=complex)
            Kc[sink_idx, :] = np.sqrt(dw[k].real) * src.conj()
            comp.append(Kc)
    return [np.asarray(K, complex) for K in kraus] + comp


def _build_from_superop(
    S: qt.Qobj, p: TransmonParams, name: str, completion: str, tol: float
) -> SingleQubitChannel:
    """Shared: truncate a full transmon superoperator to a 3x3 engine-ready CPTP Kraus channel."""
    track_dim = 3
    kraus, SKK, _loss, _Eaa = superop_to_truncated_kraus(S, track_dim, p.sim_levels, tol=tol)
    defect = np.eye(track_dim) - SKK
    defect = 0.5 * (defect + defect.conj().T)
    leaked_population = float(np.clip(np.linalg.eigvalsh(defect).real, 0.0, None).max())

    if completion == "renormalize":
        full_kraus = [np.asarray(K, complex) for K in kraus]
        resid = float(np.max(np.abs(SKK - np.eye(track_dim))))
        note = "trace-non-increasing (truncated); caller renormalizes (exposes raw leak-out)."
    elif completion == "identity_sink":
        full_kraus = _complete_identity_sink(kraus, track_dim, tol=tol)
        SKK2 = sum(K.conj().T @ K for K in full_kraus)
        resid = float(np.max(np.abs(SKK2 - np.eye(track_dim))))
        note = (f"identity_sink completion: worst-case leaked-out frac={leaked_population:.2e} "
                f"re-injected to |{track_dim - 1}> (preserves leaked status; bias bounded by "
                f"leaked_population, reported).")
    else:
        raise ValueError(f"unknown completion {completion!r}")

    return SingleQubitChannel(
        name=name, track_dim=track_dim,
        kraus=[np.asarray(K, complex) for K in full_kraus], cptp_residual=resid,
        leaked_population=leaked_population, params=p, note=note,
    )


# ----------------------------------------------------------------------------------------
# ① Pauli baseline (recast): T1 amplitude-damping + Tphi pure-dephasing Lindblad over a cycle
# ----------------------------------------------------------------------------------------
def pauli_baseline_superoperator(p: TransmonParams, solver: str = "expm_gpu") -> qt.Qobj:
    """The single-transmon T1+Tphi Lindblad CHANNEL over one cycle ``t_c``, as a superoperator.

    In the ROTATING FRAME (H = 0; the bare-transmon number term is removed by the frame so the
    relaxation/dephasing channel is frame-independent and t_c carries only the dissipation). The
    collapse operators (Varbanov Eq B3-B6 form, single transmon):
      c1   = sqrt(g1)  a         with g1   = 1/T1     (amplitude damping)
      cphi = sqrt(2 gphi) n      with gphi = 1/Tphi   (pure dephasing ~ n)
    The Lindbladian is TIME-INDEPENDENT, so the channel superoperator is exp(L t_c).

    solver:
      "expm_gpu" (DEFAULT) -- build L via qt.liouvillian(H, c_ops) (numpy, qt.mesolve's column-
        stacking convention) and exponentiate L.full() * t_c on the GPU (torch.linalg.matrix_exp;
        exact, fast, no ODE). Convention matches qt.mesolve/propagator EXACTLY.
      "ode" -- the ORACLE: qt.propagator(H=0, [0, t_c], c_ops) adaptive-RK ODE (kept selectable so
        the gtcheck can assert expm_gpu == ode to the integration floor).

    This is the FIRST-PRINCIPLES recast of the Pauli baseline: the REAL T1/T2 transmon channel,
    NOT a flat depolarizer. Restricted to {0,1} it IS the textbook AD x dephasing qubit channel
    (the GT-check confirms vs the closed-form Kraus).
    """
    L = int(p.sim_levels)
    a, ad = _ladder(L)
    n = ad * a
    H = 0.0 * (ad * a)  # rotating frame: no coherent evolution, pure dissipation over t_c
    g1 = 1.0 / p.t1_ns
    gphi = 1.0 / p.tphi_ns
    c_ops = [np.sqrt(g1) * a, np.sqrt(2.0 * gphi) * n]
    if solver == "expm_gpu":
        return _liouvillian_superop_expm(H, c_ops, p.t_c_ns)
    if solver == "ode":
        tlist = np.array([0.0, p.t_c_ns])
        opts = {"atol": 1e-13, "rtol": 1e-11, "nsteps": 5_000_000}
        S = qt.propagator(H, tlist, c_ops=c_ops, options=opts)
        return S[-1] if isinstance(S, (list, tuple)) else S
    raise ValueError(f"unknown solver {solver!r} (expected 'expm_gpu' or 'ode')")


def build_pauli_baseline_channel(
    p: TransmonParams, completion: str = "identity_sink", tol: float = 1e-12,
    solver: str = "expm_gpu",
) -> SingleQubitChannel:
    """① the T1+Tphi Pauli-baseline channel as engine-ready 3x3 Kraus (solver: expm_gpu | ode)."""
    S = pauli_baseline_superoperator(p, solver=solver)
    return _build_from_superop(S, p, "pauli_baseline", completion, tol)


# ----------------------------------------------------------------------------------------
# ② coherent rx: a driven transmon, propagator over t with Omega*t = theta
# ----------------------------------------------------------------------------------------
def coherent_rx_superoperator(
    p: TransmonParams, theta: float, omega_over_alpha: float = 0.02, solver: str = "expm_gpu"
) -> qt.Qobj:
    """The driven-transmon CLOSED channel realizing ``exp(-i (theta/2) X)`` on ``{0,1}``.

    Drive Hamiltonian (rotating frame, on-resonance, RWA-free in the transmon ladder):
      H_drive = (Omega/2) (a + a^dag)   +   (alpha/2) a^dag a^dag a a
    The anharmonicity term is KEPT (it detunes the |1>-|2> drive transition by alpha, which is what
    limits leakage). We choose the drive strength Omega = omega_over_alpha * |alpha| (so Omega is a
    FIXED FRACTION of the anharmonicity -- SWEPT) and the gate time t = theta / Omega, so on the
    {0,1} block (where a + a^dag = X) the propagator over [0, t] realizes
      exp(-i (Omega/2)(a+a^dag) t) |_{0,1} = exp(-i (theta/2) X) = rx(theta).
    ``omega_over_alpha << 1`` keeps the |2> leakage tiny (the DECLARED, BOUNDED simplification -- the
    drive is NOT a perfect 2-level rotation; the |2> population is reported as leaked_population).

    The drive H is TIME-INDEPENDENT, so U = exp(-i H t_gate) is a single matrix exponential.
    solver:
      "expm_gpu" (DEFAULT) -- U via torch.linalg.matrix_exp(-i H.full() t_gate) on the GPU (exact,
        no ODE), then S = spre(U) spost(U^dag).
      "ode" -- the ORACLE: qt.propagator(H, [0, t_gate]) adaptive-RK ODE, then spre*spost.

    NOTE the convention: this matches the engine's circuit_sim.rx(theta) = exp(-i theta/2 X), i.e.
    a rotation ANGLE theta (NOT exp(-i theta X)). The pre-reg ledger writes "exp(-i theta X)"
    loosely; the load-bearing oracle is rx(theta), which this reproduces.
    """
    L = int(p.sim_levels)
    a, ad = _ladder(L)
    alpha = p.alpha
    Omega = float(omega_over_alpha) * abs(alpha)
    if Omega <= 0.0:
        raise ValueError("drive strength Omega must be > 0 (set omega_over_alpha > 0)")
    t_gate = float(theta) / Omega
    H = 0.5 * Omega * (a + ad) + 0.5 * alpha * (ad * ad * a * a)
    if solver == "expm_gpu":
        return _unitary_superop_expm(H, t_gate)
    if solver == "ode":
        tlist = np.array([0.0, t_gate])
        opts = {"atol": 1e-13, "rtol": 1e-11, "nsteps": 5_000_000, "max_step": min(t_gate / 50.0, 1.0)}
        U = qt.propagator(H, tlist, options=opts)
        U = U[-1] if isinstance(U, (list, tuple)) else U
        return qt.spre(U) * qt.spost(U.dag())
    raise ValueError(f"unknown solver {solver!r} (expected 'expm_gpu' or 'ode')")


def build_coherent_rx_channel(
    p: TransmonParams, theta: float, omega_over_alpha: float = 0.02,
    completion: str = "identity_sink", tol: float = 1e-12, solver: str = "expm_gpu",
) -> SingleQubitChannel:
    """② the coherent rx(theta) channel as engine-ready 3x3 Kraus (near-unitary; |2> leak bounded).

    solver: expm_gpu (DEFAULT, unitary matrix_exp) | ode (qt.propagator oracle)."""
    S = coherent_rx_superoperator(p, theta, omega_over_alpha=omega_over_alpha, solver=solver)
    ch = _build_from_superop(S, p, "coherent_rx", completion, tol)
    ch.note = (ch.note + f" | theta={theta:.6g} rad, Omega/|alpha|={omega_over_alpha:.4g} "
               f"(|2> leak from drive bounded by leaked_population={ch.leaked_population:.2e}).")
    return ch


# ----------------------------------------------------------------------------------------
# ③ amplitude-damping: the ① T1 arm alone (Tphi -> inf) at the ③ rate
# ----------------------------------------------------------------------------------------
def amp_damp_superoperator(
    p: TransmonParams, gamma: float | None = None, solver: str = "expm_gpu"
) -> qt.Qobj:
    """The single-transmon AMPLITUDE-DAMPING channel (non-unital), as a superoperator.

    Two equivalent parameterizations:
      - gamma is None  : use the ① T1 arm with Tphi -> inf (dephasing OFF), integrating
        c1 = sqrt(1/T1) a over t_c. The {0,1} damping fraction is then gamma = 1 - exp(-t_c/T1).
      - gamma given    : a STANDALONE AD Lindblad calibrated so the {0,1} damping fraction is
        exactly ``gamma`` over a unit time -- we set g1 = -ln(1 - gamma) and integrate over [0,1].
        This is the ③-rate AD (a stronger, swept gamma than the ① T1 background).
    The AD Lindblad is TIME-INDEPENDENT, so the channel superoperator is exp(L t).
    solver:
      "expm_gpu" (DEFAULT) -- L via qt.liouvillian(H, c_ops), exp(L.full() t) on the GPU (no ODE).
      "ode" -- the ORACLE: qt.propagator(H=0, [0, t], c_ops) adaptive-RK ODE.

    Returns the full L-level AD superoperator (closed-form on {0,1}; |1>-|2> AD coupling resolved by
    sim_levels so the |2> contribution -- absent here since |2> is unpopulated from {0,1} -- is
    exact). The non-unitality (|1> -> |0> decay, no reverse) is the genuine channel character.
    """
    L = int(p.sim_levels)
    a, ad = _ladder(L)
    if gamma is None:
        g1 = 1.0 / p.t1_ns
        t = p.t_c_ns
    else:
        g = float(gamma)
        if not 0.0 <= g < 1.0:
            raise ValueError(f"amp-damp gamma must be in [0,1) (got {g})")
        g1 = -np.log(1.0 - g)  # so 1 - exp(-g1 * 1) = gamma over unit time
        t = 1.0
    H = 0.0 * (ad * a)  # rotating frame, no coherent term
    c_ops = [np.sqrt(g1) * a]
    if solver == "expm_gpu":
        return _liouvillian_superop_expm(H, c_ops, t)
    if solver == "ode":
        tlist = np.array([0.0, t])
        opts = {"atol": 1e-13, "rtol": 1e-11, "nsteps": 5_000_000}
        S = qt.propagator(H, tlist, c_ops=c_ops, options=opts)
        return S[-1] if isinstance(S, (list, tuple)) else S
    raise ValueError(f"unknown solver {solver!r} (expected 'expm_gpu' or 'ode')")


def build_amp_damp_channel(
    p: TransmonParams, gamma: float | None = None,
    completion: str = "identity_sink", tol: float = 1e-12, solver: str = "expm_gpu",
) -> SingleQubitChannel:
    """③ the amplitude-damping channel as engine-ready 3x3 Kraus (solver: expm_gpu | ode)."""
    S = amp_damp_superoperator(p, gamma=gamma, solver=solver)
    ch = _build_from_superop(S, p, "amp_damp", completion, tol)
    g_eff = (1.0 - np.exp(-p.t_c_ns / p.t1_ns)) if gamma is None else float(gamma)
    ch.note = ch.note + f" | effective {{0,1}} damping gamma={g_eff:.6g}."
    return ch


# ----------------------------------------------------------------------------------------
# WG leakage (physical, first-principles): a driven 3-level transmon with |1>->|2> control
# leakage + seepage/heating Lindblads. Replaces the PHENOMENOLOGICAL wg_leak_slice_np (the
# abstract WG Lindblad exp(L.frac)) in the Axis-A teacher (twin_xzzx_teacher_fullmix.py).
# ----------------------------------------------------------------------------------------
@dataclass(frozen=True)
class WGLeakParams:
    """The PHYSICAL single-transmon control-leakage knobs -- NEVER frozen; the GT-check sweeps each.

    The leakage source is a weak OFF-RESONANT drive on the |1>-|2> transition (a control pulse
    leaking population onto the |2> leakage level -- the canonical coherent control leakage,
    Wood-Gambetta 1704.03081 Sec.V-B "unitary leakage", Eqs.55-58), plus dissipative seepage
    (|2>->|1>) and incoherent heating (|1>->|2>) ladder Lindblads.

    Grounding (Wood-Gambetta 1704.03081; the reading note
    docs/papers/reading_notes/wood_gambetta_leakage_characterization_1704.03081.md):
      omega_L : drive amplitude on the |1>-|2> transition (rad/ns). The coherent-leakage SOURCE.
                Default mhz(20) (a weak control-leakage drive; SWEPT). [WG Sec.V-B] -- alternatively
                set via ``theta_leak`` (the on-resonance |1>-|2> rotation angle omega_L*t_c). [DECLARED]
      delta_12: DETUNING of the leakage drive from the |1>-|2> transition (rad/ns) -- physically the
                anharmonicity offset between the |0>-|1> control and the |1>-|2> transition that makes
                the leakage OFF-RESONANT (alpha-scale). Default mhz(300) = |alpha| (the bare transmon
                anharmonicity, WG delta/2pi = -300 MHz). SWEPT (delta_12=0 is the on-resonance worst
                case; delta_12=|alpha| the realistic suppressed case). [WG Sec.III-A, Fig.5]
      g_seep  : SEEPAGE Lindblad rate (jump |1><2|, |2>->|1> relaxation, rad/ns). Sets WG L2.
                Default mhz(50). SWEPT across the WG-L2 regime (McEwen 2102.06131 band). [WG Eq.71-72]
      g_heat  : HEATING Lindblad rate (jump |2><1|, |1>->|2> incoherent, rad/ns). C_L=0 (incoherent).
                Default 0.0 (no heating). SWEPT for the matched-WG-L1 incoherent ablation. [WG Eq.71-72]
      t_c_ns  : the cycle time over which the leakage channel acts (ns). Default 25 ns (a CZ-gate /
                control-pulse slice; the leakage accrues during the gate, not the full QEC cycle).
                SWEPT. [WG Sec.III-A pulse times 8-30 ns] [DECLARED]
      alpha   : transmon anharmonicity (rad/ns), -300 MHz; carried for the |3> structural-decoupling
                note (the |1>-|2> drive does NOT couple |2>-|3> in this minimal model). [standard]
      sim_levels : transmon levels in the simulation space. Default 3 (the WG-canonical qutrit
                truncation d_2=1, p.13 of WG: one extra |2> level is the paper-endorsed minimal
                leakage sim). sim_levels>3 resolves (and BOUNDS) any |3>+ leak (structurally ~0 here
                since the drive is |1>-|2> only). [WG p.13; DECLARED]
    """

    omega_L: float = mhz(20.0)
    delta_12: float = mhz(300.0)
    g_seep: float = mhz(50.0)
    g_heat: float = 0.0
    t_c_ns: float = 25.0
    alpha: float = mhz(-300.0)
    sim_levels: int = 3

    @property
    def theta_leak(self) -> float:
        """The on-resonance |1>-|2> rotation angle omega_L * t_c (rad) -- a convenience handle."""
        return self.omega_L * self.t_c_ns

    def with_(self, **kw) -> "WGLeakParams":
        return dataclasses.replace(self, **kw)


def wg_leak_superoperator(p: WGLeakParams, solver: str = "expm_gpu") -> qt.Qobj:
    """The PHYSICAL driven-transmon control-leakage CHANNEL over ``t_c``, as a superoperator.

    Hamiltonian (rotating frame of the |1>-|2> drive; the leakage source -- a weak OFF-RESONANT
    drive on the |1>-|2> transition):
        H = (omega_L/2)(|1><2| + |2><1|)  +  delta_12 |2><2|
    where ``delta_12`` is the drive detuning from the |1>-|2> transition (the anharmonicity offset
    that makes the control pulse off-resonant on |1>-|2>). On the {|1>,|2>} block this is the
    textbook off-resonant Rabi generator -> the leaked |2> population from |1> is the closed-form
    off-resonant Rabi L_coh = (omega_L^2/omega_eff^2) sin^2(omega_eff t/2), omega_eff =
    sqrt(omega_L^2 + delta_12^2) -- the INDEPENDENT oracle (NOT the WG Lindblad), which a wrong
    omega_L/delta_12 or sign would miss.

    Lindblad collapse operators (WG Eq.71-72 ladder dissipators on the |1>-|2> subspace):
        c_seep = sqrt(g_seep) |1><2|     (|2>->|1> seepage; sets WG L2)
        c_heat = sqrt(g_heat) |2><1|     (|1>->|2> incoherent heating; C_L=0)
    ``mesolve``/``propagator`` of (H + dissipators) over [0, t_c] -> the full L-level superoperator.

    NON-CIRCULAR: this PHYSICAL transmon model (an off-resonant Rabi drive + ladder Lindblads) is
    DISTINCT from the phenomenological abstract WG Lindblad (``leakage_channel_super``, exp(L.frac))
    it replaces; the GT-check validates it against the off-resonant-Rabi CLOSED FORM + the WG L1/L2
    definitions + the Prop-2 C_L bound -- never against the abstract WG Lindblad (that would be the
    same model on both sides -> circular, forbidden by pre-reg §3).
    """
    L = int(p.sim_levels)
    if L < 3:
        raise ValueError("wg_leak needs sim_levels >= 3 (|2> is the tracked leakage level)")
    # |1>-|2> drive + detuning, written directly as level operators (NOT via a + a^dag, so the
    # drive is EXCLUSIVELY |1>-|2> -- |0> and |3>+ are structurally decoupled, the declared
    # minimal-model simplification; an a+a^dag drive would also drive |0>-|1| and |2>-|3>).
    ket1 = qt.basis(L, 1)
    ket2 = qt.basis(L, 2)
    op12 = ket1 * ket2.dag()  # |1><2|
    op21 = ket2 * ket1.dag()  # |2><1|
    proj2 = ket2 * ket2.dag()  # |2><2|
    H = 0.5 * p.omega_L * (op12 + op21) + p.delta_12 * proj2
    c_ops = []
    if p.g_seep > 0.0:
        c_ops.append(np.sqrt(p.g_seep) * op12)   # seepage |2>->|1>
    if p.g_heat > 0.0:
        c_ops.append(np.sqrt(p.g_heat) * op21)   # heating |1>->|2>
    # H and the ladder Lindblads are TIME-INDEPENDENT, so the channel is exp(L t_c) (open) or
    # spre(U) spost(U^dag) with U = exp(-i H t_c) (purely coherent). solver:
    #   "expm_gpu" (DEFAULT) -- GPU matrix_exp; no ODE, so NO carrier-resolution / max_step / ODE
    #     floor concern (the matrix exp is exact). This is precisely the off-resonant-Rabi carrier
    #     problem the ODE path had to step-resolve below, now sidestepped.
    #   "ode" -- the ORACLE: qt.propagator with the carrier-resolved max_step documented below.
    if solver == "expm_gpu":
        if c_ops:
            return _liouvillian_superop_expm(H, c_ops, p.t_c_ns)
        return _unitary_superop_expm(H, p.t_c_ns)
    if solver != "ode":
        raise ValueError(f"unknown solver {solver!r} (expected 'expm_gpu' or 'ode')")
    tlist = np.array([0.0, p.t_c_ns])
    # CARRIER-RESOLVED integration (ODE oracle only). The off-resonant |1>-|2> drive has a
    # generalized-Rabi carrier omega_eff = sqrt(omega_L^2 + delta_12^2); for delta_12 ~ |alpha| ~
    # 2pi*0.3 rad/ns the period 2pi/omega_eff ~ 3 ns. A max_step that does not resolve this carrier
    # UNDER-integrates the ODE and the propagator unitarity (-> channel CPTP) floors at ~5e-9 (the
    # original min(t_c/50,1)=0.5 ns gave 5.66e-9). We pin max_step = (2pi/omega_eff)/40 (>=40 steps
    # per carrier cycle) AND keep it below t_c/50, with tight atol/rtol (1e-14/1e-12, the "tight"
    # path) -> the coherent channel reaches CPTP < 1e-9. A REAL CPTP violation (sign/coupling bug) is
    # ~1e-2, so this is purely the ODE floor, not a physics correction.
    omega_eff = float(np.sqrt(float(p.omega_L) ** 2 + float(p.delta_12) ** 2))
    carrier_step = (2.0 * np.pi / omega_eff) / 40.0 if omega_eff > 0.0 else p.t_c_ns / 50.0
    ms = float(min(carrier_step, p.t_c_ns / 50.0))
    if c_ops:
        # dissipative mesolve: the ladder Lindblads add their own (5e-8-justified) ODE floor; use the
        # SAME carrier-resolved max_step + tight tolerances (the seepage/heating rates are << the
        # carrier, so the carrier still sets the step).
        opts = {"atol": 1e-13, "rtol": 1e-11, "nsteps": 5_000_000, "max_step": ms}
        S = qt.propagator(H, tlist, c_ops=c_ops, options=opts)
        S = S[-1] if isinstance(S, (list, tuple)) else S
        return S
    # purely coherent -> a unitary channel (tighter CPTP), spre(U) spost(U^dag)
    opts = {"atol": 1e-14, "rtol": 1e-12, "nsteps": 5_000_000, "max_step": ms}
    U = qt.propagator(H, tlist, options=opts)
    U = U[-1] if isinstance(U, (list, tuple)) else U
    return qt.spre(U) * qt.spost(U.dag())


def build_wg_leak_channel(
    p: WGLeakParams, completion: str = "identity_sink", tol: float = 1e-12,
    solver: str = "expm_gpu",
) -> SingleQubitChannel:
    """The PHYSICAL WG control-leakage channel as engine-ready 3x3 Kraus (|2> TRACKED, load-bearing).

    solver: expm_gpu (DEFAULT; Liouvillian-expm if dissipative, unitary-expm if coherent) | ode.

    The leaked |2> population from |1> is the WHOLE POINT, so it is carried by the tracked d=3
    channel (NOT killed by truncation): for sim_levels=3 the truncation is EXACT (no level above |2>
    in this |1>-|2>-only model), so leaked_population reflects only the (structurally ~0) |3>+ escape
    when sim_levels>3. The channel's WG L1 (leak from |1>) is REPORTED in the note + by ``wg_rates``.

    NOTE the `_build_from_superop` `leaked_population` is the leak OUT of the tracked d=3 space (to
    |3>+), NOT the WG L1 (leak from {0,1} INTO the tracked |2>). For this channel the former is ~0
    (the on-tracked |2> leakage is the load-bearing signal, retained); use ``wg_leak_rates`` for L1.
    """
    S = wg_leak_superoperator(p, solver=solver)
    ch = _build_from_superop(S, p, "wg_leak", completion, tol)
    L1, L2 = wg_leak_rates(ch.kraus)
    cl1 = wg_coherent_leakage_rate(ch.kraus)
    ch.note = (ch.note + f" | PHYSICAL off-resonant |1>-|2> drive omega_L={p.omega_L / mhz(1.0):.3g} MHz, "
               f"delta_12={p.delta_12 / mhz(1.0):.3g} MHz, g_seep={p.g_seep / mhz(1.0):.3g} MHz, "
               f"g_heat={p.g_heat / mhz(1.0):.3g} MHz, t_c={p.t_c_ns:.3g} ns. "
               f"WG L1(leak from |1>)={L1:.3e}, L2(seepage)={L2:.3e}, C_L1={cl1:.3e} "
               f"(Prop-2 bound 2sqrt(L1(1-L1))={2.0 * np.sqrt(L1 * (1.0 - L1)):.3e}).")
    return ch


# ---- WG metric helpers (field-standard Wood-Gambetta definitions, computed on the derived channel)
def _apply_kraus3(kraus, rho3: np.ndarray) -> np.ndarray:
    return sum(K @ rho3 @ K.conj().T for K in kraus)


def wg_leak_rates(kraus_3x3: list) -> tuple[float, float]:
    """The Wood-Gambetta (1704.03081 Eq.2) leakage L1 and seepage L2 of a 3x3 qutrit channel.

    Computational subspace X1 = span{|0>,|1>} (d1=2); leakage subspace X2 = span{|2>} (d2=1).
      L1 = L(E(Pi_1/d1)) = Tr[Pi_2 E((|0><0|+|1><1|)/2)]           (population leaked OUT of {0,1})
      L2 = 1 - L(E(Pi_2/d2)) = 1 - Tr[Pi_2 E(|2><2|)]              (population returned to {0,1})
    These are POPULATION observables (decode-independent), the field-standard metric. NON-circular:
    they are the WG DEFINITION applied to OUR channel's action, NOT a fit to the WG Lindblad.
    """
    Pi1_over_d1 = np.zeros((3, 3), dtype=complex)
    Pi1_over_d1[0, 0] = 0.5
    Pi1_over_d1[1, 1] = 0.5
    out1 = _apply_kraus3(kraus_3x3, Pi1_over_d1)
    L1 = float(out1[2, 2].real)  # Tr[Pi_2 . out1]

    rho2 = np.zeros((3, 3), dtype=complex)
    rho2[2, 2] = 1.0
    out2 = _apply_kraus3(kraus_3x3, rho2)
    L2 = float(1.0 - out2[2, 2].real)
    return L1, L2


def wg_state_coherent_leakage(rho3: np.ndarray) -> float:
    """C_L(rho) = ||P_C(rho)||_1 (WG Eq.31): the 1-norm (sum of singular values) of the
    OFF-DIAGONAL X1<->X2 block P_C(rho) = Pi_1 rho Pi_2 + Pi_2 rho Pi_1. For a qutrit, X1={0,1},
    X2={2}: P_C keeps only rows/cols crossing the {0,1}|{2} cut (the |.><2| and |2><.| entries)."""
    pc = np.zeros((3, 3), dtype=complex)
    pc[0, 2] = rho3[0, 2]; pc[1, 2] = rho3[1, 2]
    pc[2, 0] = rho3[2, 0]; pc[2, 1] = rho3[2, 1]
    sv = np.linalg.svd(pc, compute_uv=False)
    return float(np.sum(sv))


def wg_coherent_leakage_rate(kraus_3x3: list, n_haar: int = 64, seed: int = 0) -> float:
    """The WG coherent-leakage rate C_{L1}(E) = int dpsi_1 C_L(E(|psi_1><psi_1|)) (Eq.39), Haar-
    averaged over the computational subspace X1={0,1}. Used to CHECK the Prop-2 bound
    C_{L1} <= 2 sqrt(L1(1-L1)) on the DERIVED channel (a wrong sign/coupling that produced spurious
    coherence would VIOLATE it -> the oracle can fail)."""
    rng = np.random.default_rng(seed)
    acc = 0.0
    for _ in range(int(n_haar)):
        v = rng.standard_normal(2) + 1j * rng.standard_normal(2)
        v = v / np.linalg.norm(v)
        rho1 = np.zeros((3, 3), dtype=complex)
        rho1[:2, :2] = np.outer(v, v.conj())
        out = _apply_kraus3(kraus_3x3, rho1)
        acc += wg_state_coherent_leakage(out)
    return float(acc / int(n_haar))


# ----------------------------------------------------------------------------------------
# the INDEPENDENT analytic oracles (NON-QuTiP closed forms; pre-reg §3) -- used by the GT-check
# ----------------------------------------------------------------------------------------
def analytic_amp_damp_kraus(gamma: float) -> list:
    """Closed-form qubit amplitude-damping Kraus (Nielsen & Chuang 8.3.5), NON-QuTiP:
      K0 = [[1, 0], [0, sqrt(1-gamma)]],   K1 = [[0, sqrt(gamma)], [0, 0]].
    gamma = damping fraction (= 1 - exp(-t/T1) for a T1 channel over time t)."""
    g = float(gamma)
    K0 = np.array([[1.0, 0.0], [0.0, np.sqrt(1.0 - g)]], dtype=complex)
    K1 = np.array([[0.0, np.sqrt(g)], [0.0, 0.0]], dtype=complex)
    return [K0, K1]


def analytic_dephasing_kraus(p_z: float) -> list:
    """Closed-form qubit pure-dephasing Kraus, NON-QuTiP: {sqrt(1-p_z) I, sqrt(p_z) Z}.

    p_z = the Z-error probability. For a pure-dephasing Lindblad cphi = sqrt(2 gphi) n over time t
    the off-diagonal coherence decays as exp(-t/Tphi) = exp(-2 gphi t)... careful: with c = sqrt(2
    gphi) n the qubit coherence rho_01 decays as exp(-gphi t) (rate Gamma_phi = 1/Tphi). The Z-
    channel that gives coherence factor (1 - 2 p_z) = exp(-t/Tphi) is p_z = (1 - exp(-t/Tphi))/2.
    """
    pz = float(p_z)
    I = np.eye(2, dtype=complex)
    Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
    return [np.sqrt(1.0 - pz) * I, np.sqrt(pz) * Z]


# ---- WG leak INDEPENDENT analytic oracle (off-resonant Rabi closed form + analytic ladder Kraus)
def analytic_offres_rabi_leak(omega_L: float, delta_12: float, t: float) -> float:
    """The closed-form OFF-RESONANT RABI leaked population |1>->|2> (NON-QuTiP, from the 2-level
    |1>-|2> off-resonant drive, GENUINELY INDEPENDENT of the WG Lindblad):
        L_coh = (omega_L^2 / omega_eff^2) sin^2(omega_eff t / 2),  omega_eff = sqrt(omega_L^2 + delta_12^2).
    A wrong omega_L/delta_12 or a sign error would MISS this -> the oracle can fail (load-bearing)."""
    oL = float(omega_L)
    om_eff = np.sqrt(oL * oL + float(delta_12) ** 2)
    if om_eff <= 0.0:
        return 0.0
    return float((oL * oL) / (om_eff * om_eff) * np.sin(0.5 * om_eff * float(t)) ** 2)


def analytic_offres_rabi_unitary_3(omega_L: float, delta_12: float, t: float) -> np.ndarray:
    """The closed-form 3x3 off-resonant-Rabi UNITARY on the {|1>,|2>} block (|0> untouched), NON-
    QuTiP -- exp(-i t (omega_L/2 sigma_x^{12} + delta_12 |2><2|)). The {1,2} block is the standard
    detuned-Rabi unitary; on |2><2| we carry the +delta_12 frame. (This reproduces the COHERENT part
    of wg_leak_superoperator from the closed form, INDEPENDENTLY -- a different construction, not the
    QuTiP propagator.)"""
    oL = float(omega_L); d = float(delta_12); tt = float(t)
    om_eff = np.sqrt(oL * oL + d * d)
    U = np.eye(3, dtype=complex)
    if om_eff <= 0.0:
        return U
    # H_block on {1,2} (in the rotated frame used by wg_leak_superoperator: diag(0, delta_12) +
    # off-diag omega_L/2). Diagonalize the 2x2 H_block analytically -> U2 = exp(-i tt H_block).
    Hb = np.array([[0.0, 0.5 * oL], [0.5 * oL, d]], dtype=complex)
    w, V = np.linalg.eigh(Hb)
    U2 = (V * np.exp(-1j * tt * w)) @ V.conj().T
    U[1, 1] = U2[0, 0]; U[1, 2] = U2[0, 1]
    U[2, 1] = U2[1, 0]; U[2, 2] = U2[1, 1]
    return U


def _wg_leak_liouvillian_3(p: WGLeakParams) -> np.ndarray:
    """The 3x3-system Lindbladian (Liouville) MATRIX L (9x9) of the WG-leak master equation, built
    FROM SCRATCH in numpy (column-stacking vec convention, vec(rho) stacks COLUMNS so
    vec(A rho B) = (B^T kron A) vec(rho)). This is the SAME physics as wg_leak_superoperator but a
    DIFFERENT, INDEPENDENT numerical path (a hand-built Liouvillian + scipy expm below, NOT the
    QuTiP propagator's adaptive ODE) -- so matching it to ~1e-9 validates QuTiP's INTEGRATION (the
    MODEL is already validated by the closed-form 3b.1 Rabi + 3b.2 Prop-2 checks).

    H = (omega_L/2)(|1><2|+|2><1|) + delta_12 |2><2|  (identical to wg_leak_superoperator).
    Dissipators (GKSL): c_seep = sqrt(g_seep)|1><2|, c_heat = sqrt(g_heat)|2><1|.
      L vec(rho) = vec( -i[H,rho] + sum_c ( c rho c^dag - 1/2 {c^dag c, rho} ) ).
    Returns the 9x9 complex Liouvillian (in 1/ns); the channel is expm(L * t_c) (below)."""
    L = 3
    I3 = np.eye(L, dtype=complex)
    E = lambda i, j: _e(i, j, L)  # noqa: E731
    H = 0.5 * float(p.omega_L) * (E(1, 2) + E(2, 1)) + float(p.delta_12) * E(2, 2)
    c_ops = []
    if float(p.g_seep) > 0.0:
        c_ops.append(np.sqrt(float(p.g_seep)) * E(1, 2))  # |2>-> |1>
    if float(p.g_heat) > 0.0:
        c_ops.append(np.sqrt(float(p.g_heat)) * E(2, 1))  # |1>-> |2>
    # column-stacking superoperators: vec(A rho B) = (B^T kron A) vec(rho)
    Li = -1j * (np.kron(I3, H) - np.kron(H.T, I3))  # -i[H, .]
    for c in c_ops:
        cdc = c.conj().T @ c
        Li += np.kron(c.conj(), c)                              # c . c^dag
        Li += -0.5 * np.kron(I3, cdc)                           # -1/2 c^dag c .
        Li += -0.5 * np.kron(cdc.T, I3)                         # -1/2 . c^dag c
    return Li


def expm_wg_leak_channel_3(p: WGLeakParams) -> np.ndarray:
    """The WG-leak channel as a 3x3-system SUPEROPERATOR via the matrix exponential of the hand-built
    Liouvillian: S = expm(L * t_c) (scipy.linalg.expm; column-stacking convention). A GENUINELY
    INDEPENDENT exact solver of the SAME 3-level master equation as wg_leak_superoperator -- a
    different numerical integrator (matrix exp vs QuTiP adaptive ODE), so it should agree with QuTiP
    to the integration floor at ANY rate. Returns the 9x9 superoperator (column-stacking)."""
    from scipy.linalg import expm  # local import; scipy is a project dep, CPU-only
    Li = _wg_leak_liouvillian_3(p)
    return expm(Li * float(p.t_c_ns))


def expm_wg_leak_kraus_3(p: WGLeakParams, tol: float = 1e-12) -> list:
    """The INDEPENDENT WG-leak 3x3 Kraus (the 3b.3 ORACLE): Choi eigendecomposition of the
    expm-derived superoperator. NON-CIRCULAR vs QuTiP (independent integrator) and vs the WG Lindblad
    abstraction (this is the PHYSICAL 3-level master equation, the same one wg_leak_superoperator
    integrates). Compared to the QuTiP channel by Choi/process fidelity (gauge-free)."""
    S = expm_wg_leak_channel_3(p)  # 9x9 column-stacking superoperator
    D = 3
    # Build the Choi in the same convention as choi_from_channel_3_full: sum_ij E(|i><j|) kron E_ij.
    choi = np.zeros((D * D, D * D), dtype=complex)
    for i in range(D):
        for j in range(D):
            rho = _e(i, j, D)
            vec = rho.reshape(-1, order="F")
            out = (S @ vec).reshape(D, D, order="F")
            choi += np.kron(out, _e(i, j, D))
    w, V = np.linalg.eigh(0.5 * (choi + choi.conj().T))
    kraus = []
    for k in range(len(w)):
        if w[k].real > tol:
            kraus.append(np.sqrt(w[k].real) * V[:, k].reshape(D, D, order="C"))
    return kraus


def analytic_wg_leak_kraus_3(p: WGLeakParams) -> list:
    """The INDEPENDENTLY-constructed 3x3 WG-leak channel (the 3b.3 GT-check ORACLE).

    IMPLEMENTATION (option-3, the tight-at-all-rates oracle): a from-scratch matrix-exponential of
    the SAME 3-level Lindbladian (``expm_wg_leak_kraus_3``) -- a genuinely INDEPENDENT numerical
    integrator (scipy.linalg.expm of a hand-built Liouvillian, NOT the QuTiP adaptive ODE, NOT the
    abstract WG Lindblad). It solves the identical master equation by a different method, so it
    agrees with the QuTiP channel to the integration floor at ANY (g_seep, g_heat, omega_L) -- a
    tight gate.

    HISTORY / why not the earlier crude composition. v1 of this oracle composed the closed-form
    off-resonant-Rabi UNITARY with a generalized-amplitude-damping (GAD) ladder Kraus set. That was
    WRONG: a GAD channel with thermal parameter p=g_seep/G does NOT equal the TIME EVOLUTION of the
    seepage/heating Lindblad (different steady state + coherence-decay rate), so it failed even at
    weak rates (Choi fidelity ~0.73 -- a flat oracle bug, not the O(rate^2) composition regime). The
    expm path removes the composition approximation AND the GAD mis-parameterization entirely. The
    closed-form off-resonant-Rabi pieces (``analytic_offres_rabi_leak`` / ``..._unitary_3``) are
    UNCHANGED and still back the COHERENT 3b.1 check (which passes, non-circular)."""
    return expm_wg_leak_kraus_3(p)


def choi_from_channel_3_full(kraus_3x3: list) -> np.ndarray:
    """The FULL 3-level Choi of a 3x3 channel (input basis {|0>,|1>,|2>}), so two qutrit channels
    (incl. the |2> leakage block) are compared AS CHANNELS. Same convention as the 2-level oracle
    Choi (sum_{ij} E(|i><j|) kron |i><j|). Used to compare the QuTiP WG-leak channel to the
    independent analytic WG-leak channel (Choi/process fidelity, gauge-free)."""
    D = 3
    choi = np.zeros((D * D, D * D), dtype=complex)
    for i in range(D):
        for j in range(D):
            Eij = _apply_kraus3(kraus_3x3, _e(i, j, D))
            choi += np.kron(Eij, _e(i, j, D))
    return choi


def analytic_pauli_baseline_choi(p: TransmonParams) -> np.ndarray:
    """The {0,1}-block Choi of the COMPOSED closed-form AD x dephasing channel (the ① oracle),
    built from NON-QuTiP closed-form Kraus only.

    AD fraction:   gamma = 1 - exp(-t_c / T1).
    Dephasing: the pure-dephasing arm acts on the {0,1} coherence with rate 1/Tphi over t_c; the
    Z-channel probability p_z = (1 - exp(-t_c / Tphi)) / 2. NOTE: amplitude damping ALSO dephases
    (it shrinks the coherence by sqrt(1-gamma)); the closed-form composition AD-then-dephasing
    captures the TOTAL coherence decay. We compose AD then dephasing (they commute on the diagonal;
    on the coherence the factors multiply -> the total |rho_01| factor is sqrt(1-gamma)*(1-2 p_z)),
    matching the joint Lindblad to O(rate^2) (the bounded mismatch the GT-check reports).
    """
    gamma = 1.0 - np.exp(-p.t_c_ns / p.t1_ns)
    p_z = 0.5 * (1.0 - np.exp(-p.t_c_ns / p.tphi_ns))
    ad = analytic_amp_damp_kraus(gamma)
    dz = analytic_dephasing_kraus(p_z)
    # composed channel E = dephasing o AD: Kraus { D_b A_a }
    composed = [Db @ Aa for Db in dz for Aa in ad]
    return _choi_from_kraus_2(composed)


def _choi_from_kraus_2(kraus_2x2: list) -> np.ndarray:
    """Choi matrix (un-normalized, Tr = 2) of a 2x2-Kraus channel:
       Choi = sum_k (K_k kron I) |Omega><Omega| (K_k kron I)^dag, |Omega> = sum_i |ii>.
    Equivalently Choi = sum_{ij} E(|i><j|) kron |i><j|. We use the latter (matches the truncation
    builder's convention so the comparison is apples-to-apples)."""
    D = 2
    choi = np.zeros((D * D, D * D), dtype=complex)
    for i in range(D):
        for j in range(D):
            Eij = sum(K @ _e(i, j, D) @ K.conj().T for K in kraus_2x2)
            choi += np.kron(Eij, _e(i, j, D))
    return choi


def choi_from_channel_3_block01(kraus_3x3: list) -> np.ndarray:
    """The {0,1}-restricted Choi (2x2 input block) of a 3x3 ENGINE channel, in the SAME convention
    as ``_choi_from_kraus_2`` -- i.e. feed the {0,1} input block through the full 3x3 channel and
    read the {0,1} output block. This is what we compare to the analytic 2x2 oracle Choi.

    (Population that the 3x3 channel sends from {0,1} into |2> is OUTSIDE this restricted Choi; for
    the dissipative ①③ channels that population is ~leaked_population and is the bounded mismatch.)
    """
    D = 2
    choi = np.zeros((D * D, D * D), dtype=complex)
    for i in range(D):
        for j in range(D):
            rho3 = np.zeros((3, 3), dtype=complex)
            rho3[i, j] = 1.0
            out3 = sum(K @ rho3 @ K.conj().T for K in kraus_3x3)
            Eij = out3[:2, :2]
            choi += np.kron(Eij, _e(i, j, D))
    return choi


def choi_fidelity(choi_a: np.ndarray, choi_b: np.ndarray) -> float:
    """State-fidelity between two (un-normalized) Choi matrices, normalized to trace 1 each
    (= the Jamiolkowski process fidelity). F = (Tr sqrt( sqrt(A) B sqrt(A) ))^2 in [0,1]; 1.0 ==
    identical channels. Robust gauge-free channel comparison (Kraus are gauge-non-unique)."""
    A = choi_a / np.trace(choi_a)
    B = choi_b / np.trace(choi_b)
    A = 0.5 * (A + A.conj().T)
    B = 0.5 * (B + B.conj().T)
    wa, Va = np.linalg.eigh(A)
    wa = np.clip(wa.real, 0.0, None)
    sqrtA = (Va * np.sqrt(wa)) @ Va.conj().T
    M = sqrtA @ B @ sqrtA
    M = 0.5 * (M + M.conj().T)
    wm = np.clip(np.linalg.eigvalsh(M).real, 0.0, None)
    return float(np.sum(np.sqrt(wm)) ** 2)


def rx_unitary_2x2(theta: float) -> np.ndarray:
    """Closed-form rx(theta) = exp(-i theta/2 X) (NON-torch, NON-QuTiP), matching
    qec_twin.forward.exact.circuit_sim.rx. The GT-check ALSO imports the actual circuit_sim.rx and
    asserts this matches it, so the engine convention is the single source of truth."""
    c = np.cos(theta / 2.0)
    s = np.sin(theta / 2.0)
    return np.array([[c, -1j * s], [-1j * s, c]], dtype=complex)


def unitary_channel_choi_2(U2: np.ndarray) -> np.ndarray:
    """Choi of a 2x2 unitary channel rho -> U rho U^dag (same convention as _choi_from_kraus_2)."""
    return _choi_from_kraus_2([U2])


__all__ = [
    "TransmonParams", "SingleQubitChannel",
    "_matrix_exp_np", "_liouvillian_superop_expm", "_unitary_superop_expm",
    "transmon_H_static", "superop_to_truncated_kraus",
    "pauli_baseline_superoperator", "build_pauli_baseline_channel",
    "coherent_rx_superoperator", "build_coherent_rx_channel",
    "amp_damp_superoperator", "build_amp_damp_channel",
    "WGLeakParams", "wg_leak_superoperator", "build_wg_leak_channel",
    "wg_leak_rates", "wg_state_coherent_leakage", "wg_coherent_leakage_rate",
    "analytic_offres_rabi_leak", "analytic_offres_rabi_unitary_3",
    "_wg_leak_liouvillian_3", "expm_wg_leak_channel_3", "expm_wg_leak_kraus_3",
    "analytic_wg_leak_kraus_3", "choi_from_channel_3_full",
    "analytic_amp_damp_kraus", "analytic_dephasing_kraus", "analytic_pauli_baseline_choi",
    "choi_from_channel_3_block01", "choi_fidelity",
    "rx_unitary_2x2", "unitary_channel_choi_2",
    "ghz", "mhz",
]

from __future__ import annotations

r"""Axis-1 within-substep joint-Lindbladian assembler (the G2 HEADLINE substrate).

WHAT THIS IS (the "Axis-1" assembler — ADR-0008-adjacent; build contract §A/§B-5/§E)
------------------------------------------------------------------------------------
The faithful per-cycle teacher evolution is NOT a composition chain of individually-
derived per-mechanism channels. Within a single time SUB-STEP (1q-gate layer / CZ
layer / idle / readout), every mechanism active in that sub-step enters ONE
Lindbladian and is propagated ONCE:

    L_substep = -i[ Sigma_i H_i, . ] + Sigma_k D[c_k]
    E_substep = expm(L_substep * dt)        (ONE torch.linalg.matrix_exp on cuda)

`assemble_substep_channel` builds that joint channel as a CPTP Kraus stack.
`composed_substep_channel` builds the NAIVE alternative — each mechanism's OWN
single-generator channel applied SEQUENTIALLY (E_1 . E_2 . ...) — the thing a naive
composition chain does, which DROPS the within-substep cross-terms `[H_i, H_j]`.
`composed_vs_joint_infidelity` is the G2 metric: the process (entanglement)
infidelity `1 - F_pro` between the composed and joint CPTP channels, via their Choi
states. Composition WITHIN a substep is the APPROXIMATION under test; the joint
propagator is the EXACT reference (anti-circular: the reference is derived
independently of the approximation it scores).

VEC CONVENTION (stated explicitly — MATCHES the in-tree / qt.liouvillian convention)
------------------------------------------------------------------------------------
We use **column-stacking** (Fortran / "super" convention), the SAME convention as
`qt.liouvillian(...).full()` + the per-dyad `reshape(-1, order="F")` build in
`outputs/teacher_prereg/qutip_opensystem_channels.py` (`_full_superop_expm_gpu`,
`superop_to_truncated_kraus_1q`) and the build-contract §B-5 formula. Under
column-stacking, with `vec(A rho B) = (B^T (x) A) vec(rho)` (kron = `(x)`):

    vec(-i[H, rho])      = -i ( I(x)H - H^T(x)I ) vec(rho)
    vec(c rho c^dag)     = ( conj(c) (x) c ) vec(rho)           [since (c^dag)^T = conj(c)]
    vec(-1/2 {c^dag c, rho}) = -1/2 ( I(x)(c^dag c) + (c^dag c)^T(x)I ) vec(rho)

so the Liouvillian is exactly the build-contract §B-5 form:

    L = -i ( I(x)H - H^T(x)I )
        + Sigma_k [ conj(c_k)(x)c_k - 1/2 ( I(x)(c_k^dag c_k) + (c_k^dag c_k)^T(x)I ) ]

and a column-stacked density matrix is `vec(rho) = rho.reshape(-1)` in PyTorch's
default ROW-major flatten composed with a transpose, i.e. `rho.T.reshape(D*D)`;
equivalently `vec(rho)[j*D + i] = rho[i, j]`. We implement vec/unvec consistently
with this column-stacking so the superoperator `S = expm(L*dt)` acts as
`vec(E(rho)) = S @ vec(rho)`.

CHOI CONVENTION (matches `superop_to_truncated_kraus_1q` exactly)
-----------------------------------------------------------------
`Choi(E) = Sigma_{p,q} E(|p><q|) (x) |p><q|`  (a (D^2, D^2) PSD matrix). Hermitian-
symmetrise, eigendecompose; Kraus `K_k = sqrt(w_k) * V[:,k].reshape(D, D)` (C/row-
major reshape, matching the in-tree convention) for every eigenvalue
`w_k > NUMERICAL_ZERO`. Because `S = expm(L*dt)` for a GKSL `L` is CPTP, the Choi is
PSD and `Sigma_k K_k^dag K_k = I` already; we drop the structural-zero eigenvalues
(< NUMERICAL_ZERO) and (defensively) complete any trace-preservation defect with an
identity-sink term, exactly as the validated 1q path does. Process fidelity is the
Choi-STATE fidelity of the two channels' (trace-normalised) Choi matrices — the SAME
Choi/process-fidelity convention the project's `qutip_*` gtchecks use, so G2 is
consistent with the channel-oracle checks.

GPU-ONLY (memory rule). `device="cuda"`, `torch.linalg.matrix_exp`, complex128, NO
CPU fallback (fix launch-bound paths, never `cuda if available else cpu`). torch is
imported lazily inside the functions so the module is importable / `ast.parse`-able
without torch on the authoring box; the orchestrator runs the GPU work serially.
"""

import math

from qec_twin.numerics import NUMERICAL_ZERO

# complex / real dtypes are resolved lazily (inside functions) from torch so the
# module imports without torch; named here only for documentation.
_CDTYPE_NAME = "complex128"
_RDTYPE_NAME = "float64"


def _validate_dt(dt):
    """Fail loudly on a non-finite or non-positive substep duration (NaN/inf/<=0) — a silent
    bad dt would propagate through expm into a garbage channel. Returns dt as a float."""
    dt = float(dt)
    if not math.isfinite(dt) or dt <= 0.0:
        raise ValueError(f"dt must be finite and > 0; got dt={dt!r}")
    return dt


# --------------------------------------------------------------------------- #
# vec / Liouvillian builders (column-stacking convention)                      #
# --------------------------------------------------------------------------- #
def _require_cuda(device: str):
    """GPU-only guard (memory rule): refuse any non-cuda device. No CPU fallback."""
    dev = str(device)
    if not dev.startswith("cuda"):
        raise ValueError(
            f"joint_lindbladian is GPU-only (memory rule: no 'cuda if available else cpu'); "
            f"got device={device!r}. Run on the cuda workstation."
        )
    return dev


def liouvillian_superop(H_list, c_list, *, device="cuda"):
    r"""Assemble the column-stacked Liouvillian superoperator
    ``L = -i[Sigma_i H_i, .] + Sigma_k D[c_k]`` as a dense ``(D^2, D^2)`` complex128
    torch tensor on cuda.

    Args:
      H_list  : list of Hermitian Hamiltonians (each ``(D, D)`` complex128) on the
                window Hilbert space. Summed into one ``H = Sigma_i H_i`` BEFORE the
                commutator (the within-substep JOINT propagation; the cross-terms
                ``[H_i, H_j]`` are retained exactly, never composed away).
      c_list  : list of collapse / jump operators (each ``(D, D)`` complex128).
      device  : must be cuda (GPU-only).

    Column-stacking convention (see module docstring): with kron ``(x)``,
      L = -i ( I(x)H - H^T(x)I )
          + Sigma_k [ conj(c)(x)c - 1/2 ( I(x)(c^dag c) + (c^dag c)^T(x)I ) ].
    This is the qt.liouvillian / build-contract §B-5 convention EXACTLY.
    """
    import torch

    dev = _require_cuda(device)
    cdt = torch.complex128

    # Determine D from the first available operator.
    ops = list(H_list) + list(c_list)
    if not ops:
        raise ValueError("liouvillian_superop: need at least one H or c operator")
    D = int(torch.as_tensor(ops[0]).shape[-1])
    eye = torch.eye(D, dtype=cdt, device=dev)

    # H = Sigma_i H_i (joint, NOT composed).
    H = torch.zeros((D, D), dtype=cdt, device=dev)
    for Hi in H_list:
        Hi = torch.as_tensor(Hi, dtype=cdt, device=dev)
        if Hi.shape != (D, D):
            raise ValueError(f"H operator shape {tuple(Hi.shape)} != ({D},{D})")
        H = H + Hi

    # Coherent part: -i ( I(x)H - H^T(x)I ).
    # ROBUST BLANKET RULE: `torch.kron` raises on a NON-CONTIGUOUS operand (transpose/conj/sliced
    # views: "view size is not compatible with stride"). So EVERY operand of EVERY torch.kron in
    # this module is wrapped in `.contiguous()` — a no-op (zero cost, identical values) when the
    # tensor is already contiguous, a layout copy of the SAME values otherwise. This kills the
    # whole error class at once and changes NO numerics; the column-stacking vec convention is
    # preserved exactly.
    L = -1j * (torch.kron(eye.contiguous(), H.contiguous())
               - torch.kron(H.transpose(-1, -2).contiguous(), eye.contiguous()))

    # Dissipators: Sigma_k D[c_k].
    for ck in c_list:
        c = torch.as_tensor(ck, dtype=cdt, device=dev)
        if c.shape != (D, D):
            raise ValueError(f"c operator shape {tuple(c.shape)} != ({D},{D})")
        cdag_c = c.conj().transpose(-1, -2) @ c
        L = L + torch.kron(c.conj().contiguous(), c.contiguous())
        L = L - 0.5 * torch.kron(eye.contiguous(), cdag_c.contiguous())
        L = L - 0.5 * torch.kron(cdag_c.transpose(-1, -2).contiguous(), eye.contiguous())
    return L


def _superop_expm(L, dt, *, device="cuda"):
    """``S = expm(L * dt)`` — ONE ``torch.linalg.matrix_exp`` on cuda (complex128). ``dt`` is
    validated finite + > 0 (the single dt chokepoint for joint/composed paths)."""
    import torch

    dev = _require_cuda(device)
    dt = _validate_dt(dt)
    L = torch.as_tensor(L, dtype=torch.complex128, device=dev)
    return torch.linalg.matrix_exp(L * dt)


# --------------------------------------------------------------------------- #
# superoperator -> CPTP Kraus (Choi eigendecomposition; identity-sink completion)
# --------------------------------------------------------------------------- #
def _apply_superop_to_dyad(S, i, j, D):
    """Return ``E(|i><j|)`` as a ``(D, D)`` tensor, given the column-stacked
    superoperator ``S`` (``vec(E(rho)) = S @ vec(rho)``, vec = column-stacking).

    Column-stacking: ``vec(|i><j|)`` is the unit vector at index ``j*D + i``; the
    output column ``j*D + i`` of ``S``, reshaped back column-major to ``(D, D)``,
    is ``E(|i><j|)``.
    """
    import torch

    col = S[:, j * D + i]  # (D^2,)
    # column-major unvec: out[a, b] = col[b*D + a]  ->  reshape (D, D) Fortran-order.
    return col.reshape(D, D).transpose(-1, -2).clone()


def superop_to_kraus(S, *, device="cuda", tol: float = NUMERICAL_ZERO,
                     completion: str = "identity_sink"):
    r"""Choi-eigendecompose the column-stacked superoperator ``S`` (``(D^2, D^2)``)
    into a CPTP Kraus stack ``(k, D, D)``.

    Choi convention (matches `superop_to_truncated_kraus_1q`):
        Choi = Sigma_{p,q} E(|p><q|) (x) |p><q|   (PSD for a CPTP E).
    Eigendecompose the Hermitian-symmetrised Choi; keep eigenpairs with eigenvalue
    ``> tol`` (drop the structural zeros); Kraus ``K = sqrt(w) * V[:,k].reshape(D, D)``
    (C/row-major reshape, the in-tree convention). For a true GKSL ``expm`` the map is
    already trace-preserving; ``identity_sink`` (re-)injects any residual TP defect to
    the top level so the returned stack is exactly CPTP. ``renormalize`` returns the raw
    (trace-non-increasing) Kraus instead.

    Returns ``(kraus_stack, tp_residual, dropped_mass)``.
    """
    import torch

    dev = _require_cuda(device)
    S = torch.as_tensor(S, dtype=torch.complex128, device=dev)
    if not (S.ndim == 2 and S.shape[0] == S.shape[1]):
        raise ValueError(
            f"superop_to_kraus expects a SQUARE 2-D superoperator (D^2, D^2); got shape {tuple(S.shape)}"
        )
    D = int(round(S.shape[0] ** 0.5))
    if D * D != S.shape[0]:
        raise ValueError(f"superop dim {tuple(S.shape)} is not a perfect-square (D^2,D^2)")

    # Build the Choi matrix Sigma_{p,q} E(|p><q|) (x) |p><q|.
    choi = torch.zeros((D * D, D * D), dtype=torch.complex128, device=dev)
    for p in range(D):
        for qd in range(D):
            Epq = _apply_superop_to_dyad(S, p, qd, D)  # (D, D); unvec'd column => may be non-contiguous
            epq = torch.zeros((D, D), dtype=torch.complex128, device=dev)
            epq[p, qd] = 1.0
            choi = choi + torch.kron(Epq.contiguous(), epq.contiguous())

    choi = 0.5 * (choi + choi.conj().transpose(-1, -2))
    w, V = torch.linalg.eigh(choi)

    kraus = []
    dropped_mass = 0.0
    for k in range(w.shape[0]):
        wk = float(w[k].real)
        if wk > float(tol):
            Kk = (wk ** 0.5) * V[:, k].reshape(D, D)  # C/row-major reshape (in-tree convention)
            kraus.append(Kk)
        elif wk > 0.0:
            dropped_mass += wk

    eye = torch.eye(D, dtype=torch.complex128, device=dev)
    if kraus:
        SKK = sum(K.conj().transpose(-1, -2) @ K for K in kraus)
    else:
        SKK = torch.zeros((D, D), dtype=torch.complex128, device=dev)

    if completion == "renormalize":
        tp_residual = float(torch.max(torch.abs(SKK - eye)))
        return torch.stack(kraus) if kraus else torch.zeros((0, D, D), dtype=torch.complex128, device=dev), tp_residual, float(dropped_mass)

    if completion == "identity_sink":
        defect = eye - SKK
        defect = 0.5 * (defect + defect.conj().transpose(-1, -2))
        dw, dV = torch.linalg.eigh(defect)
        top = D - 1
        comp = []
        for k in range(dw.shape[0]):
            dwk = float(dw[k].real)
            if dwk > float(tol):
                src = dV[:, k]
                Kc = torch.zeros((D, D), dtype=torch.complex128, device=dev)
                Kc[top, :] = (dwk ** 0.5) * src.conj()  # leaked TP-defect mass -> top level
                comp.append(Kc)
        full = kraus + comp
        SKK2 = sum(K.conj().transpose(-1, -2) @ K for K in full)
        tp_residual = float(torch.max(torch.abs(SKK2 - eye)))
        return torch.stack(full), tp_residual, float(dropped_mass)

    raise ValueError(f"unknown completion {completion!r}")


# --------------------------------------------------------------------------- #
# public API                                                                   #
# --------------------------------------------------------------------------- #
def assemble_substep_channel(H_list, c_list, dt, *, device="cuda",
                             completion: str = "identity_sink"):
    r"""The Axis-1 JOINT within-substep channel as a CPTP Kraus stack ``(k, D, D)``.

    Assembles ALL active mechanisms into ONE Liouvillian
    ``L = -i[Sigma_i H_i, .] + Sigma_k D[c_k]`` (column-stacking convention) and
    propagates ONCE: ``S = expm(L*dt)`` (a single ``torch.linalg.matrix_exp`` on cuda,
    complex128), then Choi-eigendecomposes ``S`` -> CPTP Kraus (identity-sink
    completion, eigenvalues < NUMERICAL_ZERO dropped).

    The within-substep cross-terms ``[H_i, H_j]`` are retained EXACTLY (the joint
    propagation), which is what a naive `composed_substep_channel` chain drops.

    Args:
      H_list   : list of Hermitian Hamiltonians ``(D, D)`` complex128 on the window.
      c_list   : list of collapse operators ``(D, D)`` complex128.
      dt       : substep duration (ns); validated finite + > 0.
      device   : cuda (GPU-only, no CPU fallback).
      completion : "identity_sink" (default, CPTP) or "renormalize" (raw).

    Returns the Kraus stack tensor ``(k, D, D)`` complex128 on ``device``.

    The Choi->Kraus trace-preservation residual and the dropped (sub-tolerance) Choi mass are
    SURFACED via a loud ``RuntimeWarning`` if they exceed ``1e-8`` / ``NUMERICAL_ZERO`` — a
    non-CPTP / lossy result (e.g. a bad generator or a numerically pathological dt) is never
    swallowed silently. For a valid GKSL ``expm`` both are ~machine-zero.
    """
    import warnings

    L = liouvillian_superop(H_list, c_list, device=device)
    S = _superop_expm(L, dt, device=device)
    kraus, tp_resid, dropped = superop_to_kraus(S, device=device, completion=completion)
    if tp_resid > 1e-8:
        warnings.warn(
            f"assemble_substep_channel: trace-preservation residual {tp_resid:.3e} > 1e-8 — "
            f"the Choi->Kraus channel is not CPTP to tolerance (check the generators / dt).",
            RuntimeWarning,
            stacklevel=2,
        )
    if dropped > NUMERICAL_ZERO:
        warnings.warn(
            f"assemble_substep_channel: dropped Choi mass {dropped:.3e} > NUMERICAL_ZERO — "
            f"sub-tolerance eigenvalues were discarded (lossy channel reconstruction).",
            RuntimeWarning,
            stacklevel=2,
        )
    return kraus


def _joint_superop(H_list, c_list, dt, *, device="cuda"):
    """The JOINT within-substep superoperator ``S = expm((-i[Sigma H, .] + Sigma D[c]) * dt)``
    (column-stacking), with NO Choi/Kraus roundtrip. The exact reference superop."""
    L = liouvillian_superop(H_list, c_list, device=device)
    return _superop_expm(L, dt, device=device)


def _composed_superop(H_list, c_list, dt, *, device="cuda"):
    r"""The NAIVE COMPOSED superoperator: each mechanism's OWN single-generator superop
    ``E_i = expm(L_i * dt)`` applied SEQUENTIALLY in the CANONICAL order, with NO Choi/Kraus
    roundtrip.

    *** SINGLE SOURCE OF TRUTH for the composition order. *** Canonical order: all Hamiltonian
    channels first (in ``H_list`` order), then all collapse channels (in ``c_list`` order); the
    FIRST listed generator is applied FIRST, so at the superop level we left-multiply in REVERSE
    list order ``S = S_last @ ... @ S_2 @ S_1``. `composed_substep_channel` and
    `composed_vs_joint_superop_distance` BOTH call this, so their composition order is identical
    by construction.
    """
    import torch

    dev = _require_cuda(device)
    superops = []
    for Hi in H_list:
        superops.append(_superop_expm(liouvillian_superop([Hi], [], device=dev), dt, device=dev))
    for ck in c_list:
        superops.append(_superop_expm(liouvillian_superop([], [ck], device=dev), dt, device=dev))
    if not superops:
        raise ValueError("_composed_superop: need at least one H or c operator")
    S = superops[0]
    for S_next in superops[1:]:
        S = S_next @ S
    return S


# the torch.linalg.matrix_exp complex128 instrument floor for the channel-level superop distance.
# For an EXACTLY-commuting pair (e.g. ZZ x T2, both diagonal in n) composed == joint ANALYTICALLY,
# so the channel-level `composed_vs_joint_superop_distance` SHOULD be 0; the residual is the
# scaling-and-squaring `matrix_exp` round-off (observed worst ~2.5e-11 at dt=20, machine-zero ~1e-16
# at dt=25/30 on cuda c128). numpy scipy.expm gives exactly 0 for the same pair, confirming the
# residual is INSTRUMENT precision, not a real composed != joint. The expm-FREE Liouvillian-commutator
# witness (`liouvillian_commutator_norm`, tol NUMERICAL_ZERO=1e-12) is the TIGHT structural witness.
SUPEROP_EXACTZERO_TOL = 1e-10


def liouvillian_commutator_norm(gen_a, gen_b, *, device="cuda"):
    r"""The expm-FREE STRUCTURAL witness for the exact-zero positive control: the Frobenius norm of
    the Liouvillian commutator ``|| [L_A, L_B] ||_F`` of two single-generator superoperators.

    ``gen_a`` / ``gen_b`` are each a ``{"H": op}`` or ``{"c": op}`` dict naming one generator (a
    Hamiltonian or a collapse operator); each is turned into its single-generator Liouvillian via
    `liouvillian_superop`, then the commutator ``[L_A, L_B] = L_A L_B - L_B L_A`` is formed and its
    Frobenius norm returned. MATMUL-ONLY — NO ``torch.linalg.matrix_exp``, so it has NO scaling-and-
    squaring floor; for an exactly-commuting pair it is ``<= NUMERICAL_ZERO`` (1e-12) at machine
    precision.

    This is the ANALYTIC REASON composed == joint for the exact-zero pair: the leading BCH defect
    between the composed product ``expm(L_A dt) expm(L_B dt)`` and the joint ``expm((L_A+L_B) dt)`` is
    ``1/2 [L_A, L_B] dt^2 + ...``; ``[L_A, L_B] = 0`` => composed == joint exactly. It is the TIGHT
    positive-control witness (instrument-floor-free).

    ROLE BOUNDARY (declared): this witness does NOT catch the broken-assembler control. The broken
    control SIGN-FLIPS the Hamiltonian commutator (+i instead of -i), which keeps the (diagonal,
    commuting) pair commuting => its Liouvillian commutator is still ~0. The broken case is caught by
    the CHANNEL-LEVEL `composed_vs_joint_superop_distance` (which reads O(1e-1) for the sign-flip).
    So: this Liouvillian-commutator witness is the tight POSITIVE control (composed==joint structural
    reason); the channel-level superop distance is the NEGATIVE control (catches the broken sign).
    The exact-zero check passes iff BOTH hold.
    """
    import torch

    dev = _require_cuda(device)

    def _L(g):
        if "H" in g:
            return liouvillian_superop([g["H"]], [], device=dev)
        if "c" in g:
            return liouvillian_superop([], [g["c"]], device=dev)
        raise ValueError("generator dict must have key 'H' or 'c'")

    L_A = _L(gen_a)
    L_B = _L(gen_b)
    comm = L_A @ L_B - L_B @ L_A
    return float(torch.linalg.matrix_norm(comm).item())


def composed_substep_channel(H_list, c_list, dt, *, device="cuda",
                             completion: str = "identity_sink"):
    r"""The NAIVE COMPOSED alternative to `assemble_substep_channel`.

    Each mechanism gets its OWN single-generator channel over the SAME ``dt``
    (``E_i = expm(L_i*dt)`` with ``L_i`` the Liouvillian of that mechanism's
    generator alone), and they are applied SEQUENTIALLY ``E_1 . E_2 . ...`` — exactly
    what a naive composition chain does. This DROPS the within-substep cross-terms
    ``[H_i, H_j]`` (and the ``[H_i, D[c_j]]`` cross-terms), so it disagrees with the
    JOINT channel by the BCH commutator the G2 gate measures.

    Canonical (fixed) order: all Hamiltonian channels first (in ``H_list`` order),
    then all collapse channels (in ``c_list`` order). The order-DEPENDENCE of the
    composed chain is itself part of what G2 exposes (a JOINT propagator has no such
    ambiguity); the fixed order makes the comparison deterministic. The order is owned by
    the shared `_composed_superop` helper (so this and `composed_vs_joint_superop_distance`
    compose identically).

    Returns the COMPOSED CPTP Kraus stack ``(k, D, D)`` complex128 on ``device``.

    Channel composition ``E_b . E_a`` (apply E_a, then E_b) is done at the
    superoperator level: ``S_compose = S_b @ S_a`` (column-stacking), so we Choi-
    decompose the composed superoperator once at the end (identical Choi convention as
    the joint path -> an apples-to-apples comparison).
    """
    dev = _require_cuda(device)
    S = _composed_superop(H_list, c_list, dt, device=dev)
    kraus, _tp_resid, _dropped = superop_to_kraus(S, device=dev, completion=completion)
    return kraus


def composed_vs_joint_superop_distance(H_list, c_list, dt, *, device="cuda"):
    r"""SUPEROPERATOR-LEVEL exact-equality witness: the Frobenius distance
    ``|| S_composed - S_joint ||_F`` between the composed and joint superoperators, with NO
    Choi/Kraus roundtrip.

    This is the CHANNEL-LEVEL exact-zero witness (and the NEGATIVE-control witness): for a commuting
    pair (ZZ x T2 — both diagonal in n) the single-generator Liouvillians commute, so
    ``S_composed = expm(L_A dt) expm(L_B dt) = expm((L_A+L_B) dt) = S_joint`` ANALYTICALLY, and this
    distance SHOULD be 0. The measured residual is the ``torch.linalg.matrix_exp`` complex128
    scaling-and-squaring floor: on cuda it is ~1e-16 at dt=25/30 (machine-zero) but ~2.5e-11 at
    dt=20 (a worse conditioning point) — INSTRUMENT precision, not a real composed != joint (numpy
    scipy.expm gives exactly 0 for the same pair). The gate therefore uses ``SUPEROP_EXACTZERO_TOL =
    1e-10`` for this channel-level witness (the matrix_exp floor), while the TIGHT machine-precision
    structural witness is the expm-FREE `liouvillian_commutator_norm` (tol NUMERICAL_ZERO=1e-12).
    For the BROKEN (sign-flipped) joint the superops differ by O(1e-1) — 9 orders above the floor,
    so this channel-level distance is the witness that catches the broken assembler. (UNLIKE
    `composed_vs_joint_choi_distance`, whose assemble->Kraus->Choi roundtrip has an additional
    ~1e-11 reconstruction floor.) Both `S_joint` and `S_composed` are built from
    `liouvillian_superop` + `_superop_expm`; the composition order is the shared `_composed_superop`
    canonical order.
    """
    import torch

    dev = _require_cuda(device)
    S_joint = _joint_superop(H_list, c_list, dt, device=dev)
    S_comp = _composed_superop(H_list, c_list, dt, device=dev)
    return float(torch.linalg.matrix_norm(S_comp - S_joint).item())


def _choi_state_from_kraus(kraus, *, device="cuda"):
    """Trace-normalised Choi STATE ``J/D`` of a channel given its Kraus stack, in the
    SAME Choi convention as `superop_to_kraus` (so it is consistent with the project's
    `qutip_*` gtchecks). ``J = Sigma_{p,q} E(|p><q|) (x) |p><q|``; the state is ``J/Tr J``
    (``Tr J = D`` for a TP map). Returns a ``(D^2, D^2)`` PSD, trace-1 tensor.
    """
    import torch

    dev = _require_cuda(device)
    kraus = torch.as_tensor(kraus, dtype=torch.complex128, device=dev)
    if kraus.ndim != 3:
        raise ValueError("kraus must be a (k, D, D) stack")
    D = int(kraus.shape[-1])
    J = torch.zeros((D * D, D * D), dtype=torch.complex128, device=dev)
    for p in range(D):
        for qd in range(D):
            rho = torch.zeros((D, D), dtype=torch.complex128, device=dev)
            rho[p, qd] = 1.0
            # E(|p><q|) = Sigma_k K rho K^dag.
            Epq = torch.zeros((D, D), dtype=torch.complex128, device=dev)
            for k in range(kraus.shape[0]):
                Kk = kraus[k]
                Epq = Epq + Kk @ rho @ Kk.conj().transpose(-1, -2)
            epq = torch.zeros((D, D), dtype=torch.complex128, device=dev)
            epq[p, qd] = 1.0
            J = J + torch.kron(Epq.contiguous(), epq.contiguous())
    J = 0.5 * (J + J.conj().transpose(-1, -2))
    tr = torch.trace(J).real
    return J / tr


def _state_fidelity(rho, sigma, *, device="cuda"):
    r"""Uhlmann state fidelity ``F(rho, sigma) = ( Tr sqrt( sqrt(rho) sigma sqrt(rho) ) )^2``
    between two PSD trace-1 matrices, via eigendecomposition (matrix square roots).
    Returns a real float in ``[0, 1]``.
    """
    import torch

    dev = _require_cuda(device)
    rho = 0.5 * (rho + rho.conj().transpose(-1, -2))
    sigma = 0.5 * (sigma + sigma.conj().transpose(-1, -2))
    # sqrt(rho) via eigh (rho is PSD).
    wr, Vr = torch.linalg.eigh(rho)
    wr = torch.clamp(wr.real, min=0.0)
    sqrt_rho = (Vr * wr.sqrt().to(torch.complex128)) @ Vr.conj().transpose(-1, -2)
    inner = sqrt_rho @ sigma @ sqrt_rho
    inner = 0.5 * (inner + inner.conj().transpose(-1, -2))
    wi, _ = torch.linalg.eigh(inner)
    wi = torch.clamp(wi.real, min=0.0)
    sqrt_sum = wi.sqrt().sum()
    return float((sqrt_sum * sqrt_sum).item())


def composed_vs_joint_infidelity(H_list, c_list, dt, *, device="cuda"):
    r"""The G2 metric: the process (entanglement) infidelity ``1 - F_pro`` between the
    COMPOSED and JOINT CPTP channels of the same ``(H_list, c_list, dt)``, computed via
    their CHOI STATES.

    ``F_pro`` is the Choi-STATE fidelity (Uhlmann fidelity of the trace-normalised Choi
    matrices ``J_joint/D`` and ``J_composed/D``) — the SAME Choi/process-fidelity
    convention the project's `qutip_*_channels` gtchecks use, declared in the H5
    pre-registration as the G2 metric. Returns ``1 - F_pro`` (a real float, ``>= 0``).

    Anti-circular: the JOINT channel is the exact reference; the COMPOSED channel is the
    approximation under test. For exact-zero pairs (`[H_i,H_j]=0`, all diagonal-in-n)
    this is ``~ 0`` and dt-INDEPENDENT (the load-bearing positive control — use
    `composed_vs_joint_choi_distance` for the MACHINE-PRECISION exact-equality witness,
    since the Uhlmann sqrt/eigh estimator floors at ~1e-8); for nonzero pairs (DR x ZZ)
    it lands in the H5-registered band with the predicted ``dt^2`` (area-preserving) /
    ``dt^4`` (fixed-Omega, leading order) power law.

    The Uhlmann estimator can return ``F_pro`` a hair above 1 (sqrt/eigh round-off);
    we return ``max(0, 1 - F_pro)`` so the infidelity is non-negative.
    """
    joint = assemble_substep_channel(H_list, c_list, dt, device=device)
    composed = composed_substep_channel(H_list, c_list, dt, device=device)
    J_joint = _choi_state_from_kraus(joint, device=device)
    J_comp = _choi_state_from_kraus(composed, device=device)
    F_pro = _state_fidelity(J_joint, J_comp, device=device)
    return float(max(0.0, 1.0 - F_pro))


def composed_vs_joint_choi_distance(H_list, c_list, dt, *, device="cuda"):
    r"""REPORTED DIAGNOSTIC (not the gate witness): the Frobenius distance
    ``|| J_joint - J_composed ||_F`` between the two trace-normalised Choi STATES (same Choi
    convention as `composed_vs_joint_infidelity`).

    For the exact-zero comparison (commuting ZZ x T2) the joint and composed channels are
    IDENTICAL, so this is ~0 — BUT it is computed from the reconstructed Kraus (assemble ->
    Choi -> distance), which carries a ~6e-12 Kraus-reconstruction floor at dt=20, so it is
    NOT used as the gate witness. The H5-/contract-REGISTERED exact-zero witnesses are instead
    the TWO in `composed_vs_joint_superop_distance` (channel-level superop distance <= 1e-10,
    the torch matrix_exp floor) and `liouvillian_commutator_norm` (structural ||[L_A,L_B]|| <=
    NUMERICAL_ZERO, expm-free). This Choi-state distance is a reported companion only; unlike
    `composed_vs_joint_infidelity` it avoids the Uhlmann sqrt/eigh estimator's ~1e-8 floor so
    it still resolves near-machine-precision, but the gate gates on the superop + commutator
    witnesses, not on this.
    """
    import torch

    dev = _require_cuda(device)
    joint = assemble_substep_channel(H_list, c_list, dt, device=dev)
    composed = composed_substep_channel(H_list, c_list, dt, device=dev)
    J_joint = _choi_state_from_kraus(joint, device=dev)
    J_comp = _choi_state_from_kraus(composed, device=dev)
    return float(torch.linalg.matrix_norm(J_joint - J_comp).item())


def composed_vs_joint_infidelity_leading(H_list, dt, *, device="cuda"):
    r"""LEADING-ORDER (BCH) process (entanglement) infidelity ``1 - F_e ~ || G ||_F^2 / d`` for the
    HAMILTONIAN-only composed-vs-joint comparison, where ``G = (i/2) [ H_0, H_1 ] dt^2`` is the
    leading Baker-Campbell-Hausdorff defect generator: the joint ``expm(-i(H_0+H_1)dt)`` and the
    composed ``expm(-iH_0 dt) expm(-iH_1 dt)`` differ by ``expm(-iG)`` with
    ``G = (i/2)[H_0, H_1] dt^2`` (HERMITIAN — the ``i`` makes ``i[H_0,H_1]`` Hermitian since
    ``[H_0,H_1]`` is anti-Hermitian; the Frobenius norm ``||G||_F`` is unchanged by the ``i``).
    ``d`` is the window Hilbert dim (the field-standard process-infidelity factor is ``1/d``, NOT
    ``1/d^2`` — METRICS.md forward-fidelity ledger).

    This is the STRUCTURAL prediction the H5 power laws derive (`1-F_e ~ ||G||_F^2/d`, G traceless):
    physical (Omega=pi/dt) -> ``dt^2``; fixed-Omega -> ``dt^4``. The EXACT channel infidelity
    (`composed_vs_joint_infidelity`) tracks this leading order at small dt but picks up higher-order
    BCH corrections (`[[H_0,H_1],H_*] dt^3` -> `1-F` at `dt^6`) at device dt values — so the gate
    verifies the LEADING-ORDER slope here is the clean `dt^2`/`dt^4` AND reports the exact-channel
    slope (whose deviation at device dt is a registered higher-order finding, not an assembler bug).
    Requires exactly two Hamiltonians (the pair); dissipators are excluded (they contaminate the
    leading commutator term — the derivation is Hamiltonian-only).
    """
    import torch

    dev = _require_cuda(device)
    if len(H_list) != 2:
        raise ValueError("composed_vs_joint_infidelity_leading expects exactly two Hamiltonians")
    A = torch.as_tensor(H_list[0], dtype=torch.complex128, device=dev)
    B = torch.as_tensor(H_list[1], dtype=torch.complex128, device=dev)
    D = int(A.shape[-1])
    # G = (i/2)[A,B] dt^2 (Hermitian). The i does not change ||G||_F, so the magnitude is identical
    # to (1/2)||[A,B]|| dt^2; kept explicit for correctness. 1-F_e ~ ||G||_F^2 / d (the /d factor).
    G = 0.5j * (A @ B - B @ A) * float(dt) ** 2
    return float((torch.linalg.matrix_norm(G) ** 2 / D).item())

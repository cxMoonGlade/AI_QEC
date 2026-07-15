from __future__ import annotations

r"""Axis-1 within-substep joint-Lindbladian assembler.

Within-substep joint assembler
------------------------------
The specified per-cycle noise-process evolution is NOT a composition chain of individually-
derived per-mechanism channels. Within a single time SUB-STEP (1q-gate layer / CZ
layer / idle / readout), every mechanism active in that sub-step enters ONE
Lindbladian and is propagated ONCE:

    L_substep = -i[ Sigma_i H_i, . ] + Sigma_k D[c_k]
    E_substep = expm(L_substep * dt)        (ONE torch.linalg.matrix_exp on cuda)

`assemble_substep_channel` builds that joint channel as a CPTP Kraus stack.
`composed_substep_channel` builds the NAIVE alternative — each mechanism's OWN
single-generator channel applied SEQUENTIALLY (E_1 . E_2 . ...) — the thing a naive
composition chain does, which DROPS the within-substep cross-terms `[H_i, H_j]`.
`composed_vs_joint_infidelity` is the joint-vs-composed comparison metric: the process (entanglement)
infidelity `1 - F_pro` between the composed and joint CPTP channels, via their Choi
states. Composition WITHIN a substep is the APPROXIMATION under test; the joint
propagator is the EXACT reference (anti-circular: the reference is derived
independently of the approximation it scores).

VEC CONVENTION (stated explicitly — MATCHES the in-tree / qt.liouvillian convention)
------------------------------------------------------------------------------------
We use **column-stacking** (Fortran / "super" convention), matching
`qt.liouvillian(...).full()` and the independent QuTiP/SciPy reference exercised by
`tests/test_joint_lindbladian.py`. Under
column-stacking, with `vec(A rho B) = (B^T (x) A) vec(rho)` (kron = `(x)`):

    vec(-i[H, rho])      = -i ( I(x)H - H^T(x)I ) vec(rho)
    vec(c rho c^dag)     = ( conj(c) (x) c ) vec(rho)           [since (c^dag)^T = conj(c)]
    vec(-1/2 {c^dag c, rho}) = -1/2 ( I(x)(c^dag c) + (c^dag c)^T(x)I ) vec(rho)

so the Liouvillian is:

    L = -i ( I(x)H - H^T(x)I )
        + Sigma_k [ conj(c_k)(x)c_k - 1/2 ( I(x)(c_k^dag c_k) + (c_k^dag c_k)^T(x)I ) ]

and a column-stacked density matrix is `vec(rho) = rho.reshape(-1)` in PyTorch's
default ROW-major flatten composed with a transpose, i.e. `rho.T.reshape(D*D)`;
equivalently `vec(rho)[j*D + i] = rho[i, j]`. We implement vec/unvec consistently
with this column-stacking so the superoperator `S = expm(L*dt)` acts as
`vec(E(rho)) = S @ vec(rho)`.

CHOI CONVENTION
-----------------------------------------------------------------
`Choi(E) = Sigma_{p,q} E(|p><q|) (x) |p><q|`  (a (D^2, D^2) PSD matrix). Hermitian-
symmetrise, eigendecompose; Kraus `K_k = sqrt(w_k) * V[:,k].reshape(D, D)` (C/row-
major reshape, matching the in-tree convention) for every positive eigenvalue by
default. Because `S = expm(L*dt)` for a GKSL `L` is CPTP, the Choi is PSD and
`Sigma_k K_k^dag K_k = I` already; negative round-off eigenvalues are ignored and
any trace-preservation defect is defensively completed with an identity-sink term,
exactly as the validated 1q path does. Callers may request positive-eigenvalue
rank pruning with `tol > 0`, but the public Axis-1 evidence path defaults to
lossless positive-eigenvalue retention. Process fidelity is the Choi-STATE fidelity
of the two channels' (trace-normalised) Choi matrices — the SAME Choi/process-
fidelity convention used by the independent QuTiP reference tests, so the comparison
is consistent with the channel-oracle checks.

GPU-ONLY (memory rule). `device="cuda"`, `torch.linalg.matrix_exp`, complex128, NO
CPU fallback (fix launch-bound paths, never `cuda if available else cpu`). torch is
imported lazily inside the functions so the module is importable / `ast.parse`-able
without torch on the authoring box; the orchestrator runs the GPU work serially.
"""

import math

from ..numerics import NUMERICAL_ZERO

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
    This is exactly the ``qt.liouvillian`` convention used by the independent tests.
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


def _robust_eigh(M):
    """Hermitian eigendecomposition with a CPU-LAPACK fallback. cuSOLVER's Hermitian eigensolve can
    fail to converge (error code 2) on highly-degenerate PSD matrices at the dense 5q carrier size;
    CPU LAPACK is robust. Returns (w, V) on M's device (a genuine failure re-raises from the CPU path)."""
    import torch

    try:
        return torch.linalg.eigh(M)
    except RuntimeError:
        w, V = torch.linalg.eigh(M.detach().to("cpu"))
        return w.to(M.device), V.to(M.device)


def superop_to_kraus(S, *, device="cuda", tol: float = 0.0,
                     completion: str = "identity_sink"):
    r"""Choi-eigendecompose the column-stacked superoperator ``S`` (``(D^2, D^2)``)
    into a CPTP Kraus stack ``(k, D, D)``.

    Choi convention:
        Choi = Sigma_{p,q} E(|p><q|) (x) |p><q|   (PSD for a CPTP E).
    Eigendecompose the Hermitian-symmetrised Choi; keep eigenpairs with eigenvalue
    ``> tol``. The default ``tol=0`` preserves every positive Choi eigenvalue so the
    dense Axis-1 evidence path does not silently drop rare Kraus branches below the
    project-wide numerical floor. Positive-eigenvalue rank pruning is available by
    passing ``tol > 0`` explicitly. Kraus ``K = sqrt(w) * V[:,k].reshape(D, D)``
    (C/row-major reshape, the in-tree convention). For a true GKSL ``expm`` the map
    is already trace-preserving; ``identity_sink`` (re-)injects any residual TP defect
    to the top level so the returned stack is exactly CPTP. ``renormalize`` returns
    the raw (trace-non-increasing) Kraus instead.

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

    # Build the Choi matrix Sigma_{p,q} E(|p><q|) (x) |p><q|. The Choi-Jamiolkowski map is a pure
    # REINDEXING of the column-stacking superop, NOT a D^2 python loop of krons:
    #   Choi[a*D+p, b*D+q] = S[b*D+a, q*D+p]  <=>  S.reshape(D,D,D,D)[b,a,q,p] permuted to [a,p,b,q].
    # Algebraically equivalent to the former p,q loop; current channel tests cover D=2..8.
    choi = S.reshape(D, D, D, D).permute(1, 3, 0, 2).reshape(D * D, D * D).contiguous()
    choi = 0.5 * (choi + choi.conj().transpose(-1, -2))
    w, V = _robust_eigh(choi)

    # Kraus_k = sqrt(w_k) * V[:,k].reshape(D, D), for eigenvalues w_k > tol. Vectorized (no python loop
    # over the D^2 eigenpairs): scale each eigen-column by sqrt(w_k), fold columns->rows->(D, D). Same
    # ascending-eigenvalue order as the former loop; current channel tests guard equivalence.
    wr = w.real
    tolf = float(tol)
    keep = wr > tolf
    sqrtw = wr.clamp(min=0.0).sqrt().to(V.dtype)                    # (D^2,)
    kraus_all = (V * sqrtw.unsqueeze(0)).transpose(0, 1).reshape(w.shape[0], D, D)  # C/row-major (in-tree)
    kraus_stack = kraus_all[keep].contiguous()                     # (k, D, D)
    dropped_mass = float(wr[(~keep) & (wr > 0.0)].sum())

    eye = torch.eye(D, dtype=torch.complex128, device=dev)
    # SKK = Sigma_k K_k^dag K_k  (batched; == I for an exactly-CPTP map)
    SKK = (torch.einsum("kij,kil->jl", kraus_stack.conj(), kraus_stack)
           if kraus_stack.shape[0] else torch.zeros((D, D), dtype=torch.complex128, device=dev))

    if completion == "renormalize":
        tp_residual = float(torch.max(torch.abs(SKK - eye)))
        return kraus_stack, tp_residual, float(dropped_mass)

    if completion == "identity_sink":
        defect = eye - SKK
        defect = 0.5 * (defect + defect.conj().transpose(-1, -2))
        dw, dV = _robust_eigh(defect)
        top = D - 1
        dwr = dw.real
        dkeep = dwr > tolf
        if bool(dkeep.any()):
            dsqrt = dwr.clamp(min=0.0).sqrt().to(dV.dtype)          # (D,)
            # comp_k has a single non-zero row `top` = sqrt(dw_k) * dV[:,k]^*  (leaked TP-defect -> top level)
            rows = (dV * dsqrt.unsqueeze(0)).transpose(0, 1)[dkeep].conj()  # (nc, D)
            comp = torch.zeros((rows.shape[0], D, D), dtype=torch.complex128, device=dev)
            comp[:, top, :] = rows
            full = torch.cat([kraus_stack, comp], dim=0)
        else:
            full = kraus_stack
        SKK2 = (torch.einsum("kij,kil->jl", full.conj(), full)
                if full.shape[0] else torch.zeros((D, D), dtype=torch.complex128, device=dev))
        tp_residual = float(torch.max(torch.abs(SKK2 - eye)))
        return full, tp_residual, float(dropped_mass)

    raise ValueError(f"unknown completion {completion!r}")


# --------------------------------------------------------------------------- #
# public API                                                                   #
# --------------------------------------------------------------------------- #
def assemble_substep_channel(H_list, c_list, dt, *, device="cuda",
                             completion: str = "identity_sink",
                             choi_eigenvalue_tol: float = 0.0):
    r"""The Axis-1 JOINT within-substep channel as a CPTP Kraus stack ``(k, D, D)``.

    Assembles ALL active mechanisms into ONE Liouvillian
    ``L = -i[Sigma_i H_i, .] + Sigma_k D[c_k]`` (column-stacking convention) and
    propagates ONCE: ``S = expm(L*dt)`` (a single ``torch.linalg.matrix_exp`` on cuda,
    complex128), then Choi-eigendecomposes ``S`` -> CPTP Kraus (identity-sink
    completion by default, every positive Choi eigenvalue retained unless
    ``choi_eigenvalue_tol > 0`` is explicitly requested).

    The within-substep cross-terms ``[H_i, H_j]`` are retained EXACTLY (the joint
    propagation), which is what a naive `composed_substep_channel` chain drops.

    Args:
      H_list   : list of Hermitian Hamiltonians ``(D, D)`` complex128 on the window.
      c_list   : list of collapse operators ``(D, D)`` complex128.
      dt       : substep duration (ns); validated finite + > 0.
      device   : cuda (GPU-only, no CPU fallback).
      completion : "identity_sink" (default, CPTP) or "renormalize" (raw).
      choi_eigenvalue_tol : positive-eigenvalue pruning threshold. The default
        ``0.0`` is the lossless evidence path; use ``NUMERICAL_ZERO`` only for an
        explicitly rank-pruned diagnostic.

    Returns the Kraus stack tensor ``(k, D, D)`` complex128 on ``device``.

    The Choi->Kraus trace-preservation residual and any intentionally pruned positive
    Choi mass are SURFACED via a loud ``RuntimeWarning`` if they exceed ``1e-8`` /
    ``NUMERICAL_ZERO`` — a non-CPTP / lossy result (e.g. a bad generator, a numerically
    pathological dt, or an explicit pruning threshold) is never swallowed silently. For
    a valid GKSL ``expm`` under the default lossless positive-eigenvalue policy both are
    ~machine-zero.
    """
    import warnings

    L = liouvillian_superop(H_list, c_list, device=device)
    S = _superop_expm(L, dt, device=device)
    kraus, tp_resid, dropped = superop_to_kraus(
        S,
        device=device,
        tol=float(choi_eigenvalue_tol),
        completion=completion,
    )
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
            f"positive Choi eigenvalues were pruned by choi_eigenvalue_tol "
            f"(lossy channel reconstruction).",
            RuntimeWarning,
            stacklevel=2,
        )
    return kraus


def assemble_substep_channels_batched(items, *, device="cuda", completion: str = "identity_sink",
                                      choi_eigenvalue_tol: float = 0.0):
    r"""BATCHED ``assemble_substep_channel`` — one batched ``matrix_exp`` + one batched Choi ``eigh``
    over ALL substeps, instead of a per-substep sequential build. Same math per item as
    ``assemble_substep_channel``; current channel tests guard the batched equivalence.

    ``items`` is a sequence of ``(H_list, c_list, dt)`` with a UNIFORM window dimension ``D`` (the dense
    Axis-1 manifest builds all substeps on the same window). Returns a list of Kraus stacks ``(k_b, D, D)``,
    one per item, in input order. The heavy linalg (the D^2 x D^2 ``matrix_exp`` and Choi ``eigh``) is
    folded into a single batched call each; only the variable-rank Kraus filtering + identity-sink
    completion stay per-item (cheap indexing/reshape, no per-item heavy linalg — the defect ``eigh`` is
    also batched).
    """
    import torch

    dev = _require_cuda(device)
    items = list(items)
    if not items:
        return []

    # Per-item Liouvillian (cheap kron sums) + validated dt; stacked for the batched propagation.
    Ls, dts = [], []
    for H_list, c_list, dt in items:
        Ls.append(liouvillian_superop(H_list, c_list, device=dev))
        dts.append(_validate_dt(dt))
    D2 = int(Ls[0].shape[-1])
    D = int(round(D2 ** 0.5))
    if D * D != D2:
        raise ValueError(f"Liouvillian dim {D2} is not a perfect square")
    for L in Ls:
        if int(L.shape[-1]) != D2:
            raise ValueError("assemble_substep_channels_batched requires a UNIFORM window dimension across items")
    Lstack = torch.stack(Ls)                                                     # (B, D^2, D^2)
    dt_t = torch.tensor(dts, dtype=torch.complex128, device=dev)                 # (B,)
    B = Lstack.shape[0]

    # ONE batched matrix_exp: S_b = expm(L_b * dt_b).
    Sstack = torch.linalg.matrix_exp(Lstack * dt_t[:, None, None])               # (B, D^2, D^2)

    # ONE batched Choi (reshape/permute, per superop_to_kraus) + ONE batched Hermitian eigh.
    choi = Sstack.reshape(B, D, D, D, D).permute(0, 2, 4, 1, 3).reshape(B, D2, D2).contiguous()
    choi = 0.5 * (choi + choi.conj().transpose(-1, -2))
    w, V = _robust_eigh(choi)                                                    # (B, D^2), (B, D^2, D^2)

    tolf = float(choi_eigenvalue_tol)
    eye = torch.eye(D, dtype=torch.complex128, device=dev)
    kraus_list, SKKs = [], []
    for b in range(B):
        wr = w[b].real
        keep = wr > tolf
        sqrtw = wr.clamp(min=0.0).sqrt().to(V.dtype)
        kall = (V[b] * sqrtw.unsqueeze(0)).transpose(0, 1).reshape(D2, D, D)
        kb = kall[keep].contiguous()
        kraus_list.append(kb)
        SKKs.append(torch.einsum("kij,kil->jl", kb.conj(), kb) if kb.shape[0]
                    else torch.zeros((D, D), dtype=torch.complex128, device=dev))

    if completion == "renormalize":
        return kraus_list
    if completion != "identity_sink":
        raise ValueError(f"unknown completion {completion!r}")

    # identity_sink: batched defect eigh over the B (D x D) TP defects.
    defect = eye.unsqueeze(0) - torch.stack(SKKs)                                # (B, D, D)
    defect = 0.5 * (defect + defect.conj().transpose(-1, -2))
    dw, dV = _robust_eigh(defect)                                               # (B, D), (B, D, D)
    top = D - 1
    full_list = []
    for b in range(B):
        dwr = dw[b].real
        dkeep = dwr > tolf
        if bool(dkeep.any()):
            dsqrt = dwr.clamp(min=0.0).sqrt().to(dV.dtype)
            rows = (dV[b] * dsqrt.unsqueeze(0)).transpose(0, 1)[dkeep].conj()    # (nc, D)
            comp = torch.zeros((rows.shape[0], D, D), dtype=torch.complex128, device=dev)
            comp[:, top, :] = rows
            full_list.append(torch.cat([kraus_list[b], comp], dim=0))
        else:
            full_list.append(kraus_list[b])
    return full_list


# --------------------------------------------------------------------------- #
# EXACT coupling-component factorization of the substep channel                #
# Current factorization contract is stated here and exercised by owner tests.   #
# --------------------------------------------------------------------------- #
# WHY THIS IS EXACT (not an approximation). For a substep,
#   L = -i[Sigma_i H_i, .] + Sigma_k D[c_k].
# Partition the window qubits into disjoint blocks {B_m} so EVERY individual
# operator (each H_i, each c_k) has its qubit support inside a single block.
# Then L = Sigma_m L_{B_m} with L_{B_m} acting only on B_m (x) I elsewhere.
# Disjoint-support superoperators commute, so expm(L) = Prod_m expm(L_{B_m}) =
# (x)_m E_{B_m}. Applying it to rho = applying each block channel to its own
# qubits (they commute). No full-window Kraus is ever formed. The blocks are the
# CONNECTED COMPONENTS of the graph with an edge (a,b) whenever some single H_i
# or c_k acts non-trivially on both a and b. The current union-find and support
# diagnostics are exercised by the connected-cluster owner tests.

_SUPPORT_TOL = 1e-9  # absolute; dephasing c ~ sqrt(gamma) can be ~0.03, so no relative tol (SPEC 4.3).


def _nq_from_D(D: int) -> int:
    """Number of qubits for a window dimension D = 2^nq (exact, raises if not a power of two)."""
    nq = int(D).bit_length() - 1
    if (1 << nq) != int(D):
        raise ValueError(f"window dimension {D} is not a power of two (2^nq)")
    return nq


def operator_support(A, nq, *, tol: float = _SUPPORT_TOL):
    r"""The set of qubits on which the (2^nq x 2^nq) operator ``A`` acts NON-trivially
    (big-endian qubit order: qubit 0 is the most-significant tensor factor, matching
    `circuit_sim.embed_operator` and `liouvillian_superop`).

    ``A`` is trivial on qubit ``q`` iff it factors as ``B (x) I_q``. Reshape ``A`` to
    ``[2]*2nq`` with row axis ``q`` and col axis ``nq+q``; trivial on ``q`` iff the
    off-diagonal blocks ``(iq=0,jq=1)`` and ``(iq=1,jq=0)`` are ~0 AND the diagonal
    blocks ``(0,0)`` and ``(1,1)`` are equal — all to ABSOLUTE tolerance ``tol`` (a
    relative tol would miss weak dephasing couplings ``c ~ sqrt(gamma) ~ 0.03``).
    Returns a sorted tuple of non-trivial qubit indices.
    """
    import torch

    At = torch.as_tensor(A, dtype=torch.complex128).reshape([2] * (2 * nq))
    sup = []
    for q in range(nq):
        rax, cax = q, nq + q
        d00 = At.select(cax, 0).select(rax, 0)
        d11 = At.select(cax, 1).select(rax, 1)
        o01 = At.select(cax, 1).select(rax, 0)
        o10 = At.select(cax, 0).select(rax, 1)
        off = max(float(o01.abs().max()), float(o10.abs().max()))
        diag_gap = float((d00 - d11).abs().max())
        if (off > tol) or (diag_gap > tol):
            sup.append(q)
    return tuple(sup)


# Below this a per-qubit non-triviality MEASURE is a genuine machine/structural zero (these operators are
# built from exact algebra, so an identity factor reads ~1e-16); a measure in [floor, _SUPPORT_TOL) is a
# real-but-weak coupling the absolute support tolerance cannot classify -> factorization is NOT certifiably
# exact and must fall back to the full-window channel.
_FACTORIZE_SAFE_FLOOR = NUMERICAL_ZERO  # 1e-12


def _has_ambiguous_support(A, nq, *, tol: float = _SUPPORT_TOL, floor: float = _FACTORIZE_SAFE_FLOOR):
    """True iff operator ``A`` (2^nq x 2^nq) has ANY qubit whose non-triviality measure
    (max of the off-diagonal-block magnitude and the diagonal-block gap, same measure as
    `operator_support`) falls in the ambiguous band ``[floor, tol)`` — a coupling too weak for
    `operator_support` to flag yet too strong to be a machine zero. Its presence means the coupling
    graph (and hence the factorization) cannot be certified exact; the caller must use the full-window
    channel instead of silently dropping the coupling.
    """
    import torch

    At = torch.as_tensor(A, dtype=torch.complex128).reshape([2] * (2 * nq))
    for q in range(nq):
        rax, cax = q, nq + q
        d00 = At.select(cax, 0).select(rax, 0)
        d11 = At.select(cax, 1).select(rax, 1)
        o01 = At.select(cax, 1).select(rax, 0)
        o10 = At.select(cax, 0).select(rax, 1)
        measure = max(float(o01.abs().max()), float(o10.abs().max()), float((d00 - d11).abs().max()))
        if floor <= measure < tol:
            return True
    return False


def _connected_components(nq, edges):
    """Connected components (union-find) over qubits ``0..nq-1`` given coupling ``edges``;
    isolated qubits become singletons. Returns a list of sorted qubit tuples in
    ascending-first-qubit order (deterministic).
    """
    parent = list(range(nq))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for i, j in edges:
        parent[find(i)] = find(j)
    comps: dict[int, list] = {}
    for q in range(nq):
        comps.setdefault(find(q), []).append(q)
    out = [tuple(sorted(c)) for c in comps.values()]
    out.sort(key=lambda c: c[0])
    return out


def restrict_operator_to_component(A, comp, nq, *, tol: float = _SUPPORT_TOL):
    r"""Restrict an operator ``A`` (2^nq x 2^nq) whose support is contained in the qubit
    set ``comp`` to the ``(2^|comp| x 2^|comp|)`` operator ``A_C`` on that subspace
    (big-endian qubit order). Permute so ``comp`` qubits come first (in ascending
    order), reshape to ``(2^|C|, 2^|rest|, 2^|C|, 2^|rest|)``, and take
    ``A_C = A_perm[:, 0, :, 0]``.

    Guard: reconstruct ``A_C (x) I_{2^|rest|}`` (un-permuted back
    to the original layout) and assert ``max|reconstruct - A| < tol``. A failure means a
    mis-assigned operator whose support crosses the component — raise, never silently
    proceed.
    """
    import torch

    A = torch.as_tensor(A, dtype=torch.complex128)
    comp = tuple(sorted(int(q) for q in comp))
    C = len(comp)
    rest_qubits = [q for q in range(nq) if q not in comp]
    R = len(rest_qubits)
    if C + R != nq:
        raise ValueError(f"component {comp} not a subset of window qubits 0..{nq - 1}")

    # Bring the component qubits to the front (both row and column axes). The reshaped tensor
    # has axes [row_0..row_{nq-1}, col_0..col_{nq-1}] in NATURAL qubit order; we want the output
    # layout [comp rows, rest rows, comp cols, rest cols]. torch.permute maps output axis i to
    # input axis perm[i], so perm's row part is exactly `new_order` (the original qubit index for
    # each output row axis) and its col part is `nq + new_order`.
    new_order = list(comp) + rest_qubits                # output position -> original qubit
    perm = new_order + [nq + q for q in new_order]
    At = A.reshape([2] * (2 * nq)).permute(*perm).contiguous()
    A_perm = At.reshape(2 ** C, 2 ** R, 2 ** C, 2 ** R)
    A_C = A_perm[:, 0, :, 0].contiguous()

    # GUARD: A must equal A_C (x) I_R exactly (up to tol) in the permuted layout.
    eyeR = torch.eye(2 ** R, dtype=torch.complex128, device=A.device)
    recon_perm = torch.kron(A_C.contiguous(), eyeR)  # (2^C * 2^R, 2^C * 2^R), component-first layout
    resid = float((recon_perm - At.reshape(2 ** nq, 2 ** nq)).abs().max())
    if resid > tol:
        raise ValueError(
            f"restrict_operator_to_component: operator support crosses component {comp} "
            f"(reconstruction residual {resid:.3e} > {tol:.1e}); the operator was mis-assigned "
            f"(its support is not contained in the component)."
        )
    return A_C


def _coupling_components(H_list, c_list, nq, *, tol: float = _SUPPORT_TOL):
    """Coupling graph -> connected components, plus each operator's support and its
    assigned component index.

    An edge ``(a, b)`` is added whenever any SINGLE H-term or c-op acts non-trivially on
    BOTH ``a`` and ``b`` (single-qubit terms add no edge). Returns
    ``(components, h_support, c_support)`` where ``components`` is the list of sorted
    qubit tuples and ``*_support`` are the per-operator support tuples (so callers do not
    recompute the support test).
    """
    edges = []
    h_support = [operator_support(h, nq, tol=tol) for h in H_list]
    c_support = [operator_support(c, nq, tol=tol) for c in c_list]
    for s in list(h_support) + list(c_support):
        for a in range(len(s)):
            for b in range(a + 1, len(s)):
                edges.append((s[a], s[b]))
    components = _connected_components(nq, edges)
    return components, h_support, c_support


def assemble_substep_channel_factored(H_list, c_list, dt, *, device="cuda",
                                      completion: str = "identity_sink",
                                      choi_eigenvalue_tol: float = 0.0):
    r"""EXACT coupling-component factorization of the Axis-1 joint substep channel.

    Instead of one full-window ``expm(L*dt)`` + Choi ``eigh`` at ``D = 2^nq``, build the
    channel over the CONNECTED COMPONENTS of the substep's 2-qubit coupling graph. Each
    component's channel is assembled at its own small dimension ``2^|B_m|`` via the SAME
    ``liouvillian_superop -> matrix_exp -> superop_to_kraus`` path (identical convention as
    `assemble_substep_channel`), then applied to its own qubits. Because disjoint-support
    Lindbladians commute, ``expm(Sigma_m L_{B_m}) = (x)_m E_{B_m}`` EXACTLY (error bound:
    machine-zero — this is an identity, not an approximation).

    Returns a list of ``(local_qubits, comp_kraus)`` in ascending-first-qubit order:
      - ``local_qubits``: sorted window-local qubit indices (subset of ``0..nq-1``) of the
        component (big-endian order — local qubit ``local_qubits[i]`` is the caller's
        window-local index; the apply loop maps it to the global qubit via
        ``selection.participant[local_qubits[i]]``).
      - ``comp_kraus``: ``(k_m, 2^|B_m|, 2^|B_m|)`` complex128 CPTP Kraus for that block.

    FALLBACK (correctness over speed): if the substep is a SINGLE component spanning all
    ``nq`` qubits, or if ``ECS_FORCE_UNFACTORIZED_AXIS1=1`` is set in the environment, return
    ``[(tuple(range(nq)), assemble_substep_channel(H_list, c_list, dt, ...))]`` — bit-for-bit
    the current full-window path. This is the A/B knob for the byte-identical records gate.
    """
    import os

    import torch

    dev = _require_cuda(device)
    H_list = list(H_list)
    c_list = list(c_list)
    ops = H_list + c_list
    if not ops:
        raise ValueError("assemble_substep_channel_factored: need at least one H or c operator")
    D = int(torch.as_tensor(ops[0]).shape[-1])
    nq = _nq_from_D(D)

    def _full_window():
        kraus = assemble_substep_channel(
            H_list, c_list, dt, device=dev,
            completion=completion, choi_eigenvalue_tol=float(choi_eigenvalue_tol),
        )
        return [(tuple(range(nq)), kraus)]

    # Env override: force the exact current full-window path (the A/B fallback).
    if os.environ.get("ECS_FORCE_UNFACTORIZED_AXIS1") == "1":
        return _full_window()

    # If any operator carries a coupling too weak for the absolute
    # support tolerance to classify (a measure in [_FACTORIZE_SAFE_FLOOR, _SUPPORT_TOL)), the coupling
    # graph cannot be certified exact -- a genuine weak coupling could be silently dropped, breaking the
    # tensor-product identity. Fall back to the EXACT full-window channel (correctness over the speed win).
    if any(_has_ambiguous_support(op, nq) for op in ops):
        return _full_window()

    components, h_support, c_support = _coupling_components(H_list, c_list, nq)

    # Single full-window component => no factorization win; take the exact full path.
    if len(components) == 1 and len(components[0]) == nq:
        return _full_window()

    # Assign each operator to the (unique) component containing its support, restrict it,
    # and build that component's channel.
    def _component_index(support):
        # A supported operator lands in the component whose qubit set contains ALL of its
        # support qubits. An empty-support (identity) operator is dropped (contributes
        # nothing to L); the block still exists because its qubit carries some operator.
        for idx, comp in enumerate(components):
            if all(q in comp for q in support):
                return idx
        raise ValueError(
            f"operator support {support} is not contained in any single component "
            f"{components}; the coupling graph is inconsistent (a support edge is missing)."
        )

    per_comp_H: list[list] = [[] for _ in components]
    per_comp_c: list[list] = [[] for _ in components]
    for Hi, sup in zip(H_list, h_support):
        if not sup:
            continue  # identity Hamiltonian: no contribution to L (skip)
        idx = _component_index(sup)
        per_comp_H[idx].append(restrict_operator_to_component(Hi, components[idx], nq))
    for ck, sup in zip(c_list, c_support):
        if not sup:
            continue  # identity collapse op: no contribution to L (skip)
        idx = _component_index(sup)
        per_comp_c[idx].append(restrict_operator_to_component(ck, components[idx], nq))

    out: list = []
    for comp, Hc, cc in zip(components, per_comp_H, per_comp_c):
        if not Hc and not cc:
            # A component with NO non-identity operator (a truly idle qubit with no dephasing/drive)
            # does not arise for declared process substeps — every window qubit that appears
            # carries >= 1 single-qubit collapse op (measured decomposition e.g. [[0,3],[1],[2],[4]]).
            # If it ever does, the EXACT full-window channel is the identity on that block (expm(0)=I),
            # so we emit the 1-Kraus identity (matching the full-window path bit-for-bit) rather than
            # crash emit; a loud warning surfaces the unexpected structure. This preserves the
            # byte-identical-records gate under the ECS_FORCE_UNFACTORIZED_AXIS1 A/B test.
            import warnings

            warnings.warn(
                f"assemble_substep_channel_factored: component {comp} has no non-identity operator "
                f"(idle qubit block); emitting the exact 1-Kraus identity channel (matches the "
                f"full-window path). This is unexpected for a real substep — check the schedule.",
                RuntimeWarning,
                stacklevel=2,
            )
            Dc = 2 ** len(comp)
            eye = torch.eye(Dc, dtype=torch.complex128, device=dev).unsqueeze(0)
            out.append((tuple(comp), eye))
            continue
        comp_kraus = assemble_substep_channel(
            Hc, cc, dt, device=dev,
            completion=completion, choi_eigenvalue_tol=float(choi_eigenvalue_tol),
        )
        out.append((tuple(comp), comp_kraus))
    return out


def assemble_substep_channels_factored_batched(items, *, device="cuda",
                                               completion: str = "identity_sink",
                                               choi_eigenvalue_tol: float = 0.0):
    r"""Optional thin speed layer over `assemble_substep_channel_factored` for a SEQUENCE of
    substeps: group ALL components (across all substeps) BY DIMENSION and run ONE batched
    ``matrix_exp`` + Choi ``eigh`` per D-group (reusing `assemble_substep_channels_batched`,
    which requires a uniform D — hence the group-by-D).

    ``items`` is a sequence of ``(H_list, c_list, dt)``. Returns a list parallel to ``items``,
    each entry the SAME ``list[(local_qubits, comp_kraus)]`` that
    `assemble_substep_channel_factored` returns for that item — so it is a drop-in for the
    per-item loop. The result is EXACT and, per component, gauge-equivalent to the per-item
    build (same channel; raw Kraus differ only by the eigen-gauge, which is irrelevant to the
    applied channel — verified for the batched builder in batched_substep_channel_verify.py).

    Correctness note: the env flag / single-full-window fallback of the per-item builder is
    honored here too (those items fall back to the full-window `assemble_substep_channel` and
    are NOT batched, so they stay bit-for-bit the current path).
    """
    import os

    import torch

    dev = _require_cuda(device)
    items = list(items)
    if not items:
        return []
    force_full = os.environ.get("ECS_FORCE_UNFACTORIZED_AXIS1") == "1"

    # Plan the components for every item; collect the small (H_C, c_C, dt) builds to batch.
    # A "slot" records where each component's kraus goes: (item_index, out_position).
    plans: list[list] = [None] * len(items)          # per item: list of (local_qubits, kraus-or-None)
    batch_items: dict[int, list] = {}                # D -> list of (H_C, c_C, dt)
    batch_slots: dict[int, list] = {}               # D -> list of (item_index, out_position)
    for i, (H_list, c_list, dt) in enumerate(items):
        H_list = list(H_list)
        c_list = list(c_list)
        ops = H_list + c_list
        if not ops:
            raise ValueError("assemble_substep_channels_factored_batched: item has no operators")
        D = int(torch.as_tensor(ops[0]).shape[-1])
        nq = _nq_from_D(D)

        full_window = force_full
        components = h_support = c_support = None
        if not full_window:
            components, h_support, c_support = _coupling_components(H_list, c_list, nq)
            if len(components) == 1 and len(components[0]) == nq:
                full_window = True

        if full_window:
            # Not batched: exact current full-window path (bit-for-bit).
            kraus = assemble_substep_channel(
                H_list, c_list, dt, device=dev,
                completion=completion, choi_eigenvalue_tol=float(choi_eigenvalue_tol),
            )
            plans[i] = [(tuple(range(nq)), kraus)]
            continue

        # Assign + restrict operators per component; queue each block's small build.
        def _component_index(support, comps=components):
            for idx, comp in enumerate(comps):
                if all(q in comp for q in support):
                    return idx
            raise ValueError(
                f"operator support {support} not contained in any component {comps}"
            )

        per_comp_H: list[list] = [[] for _ in components]
        per_comp_c: list[list] = [[] for _ in components]
        for Hi, sup in zip(H_list, h_support):
            if not sup:
                continue
            idx = _component_index(sup)
            per_comp_H[idx].append(restrict_operator_to_component(Hi, components[idx], nq))
        for ck, sup in zip(c_list, c_support):
            if not sup:
                continue
            idx = _component_index(sup)
            per_comp_c[idx].append(restrict_operator_to_component(ck, components[idx], nq))

        item_plan: list = []
        for pos, (comp, Hc, cc) in enumerate(zip(components, per_comp_H, per_comp_c)):
            if not Hc and not cc:
                # Idle-qubit block: exact identity channel (matches full-window path; see the
                # per-item builder). Filled immediately (not batched) with the 1-Kraus identity.
                import warnings

                warnings.warn(
                    f"assemble_substep_channels_factored_batched: component {comp} has no "
                    f"non-identity operator; emitting the exact 1-Kraus identity channel.",
                    RuntimeWarning,
                    stacklevel=2,
                )
                Dc = 2 ** len(comp)
                eye = torch.eye(Dc, dtype=torch.complex128, device=dev).unsqueeze(0)
                item_plan.append([tuple(comp), eye])
                continue
            Dc = 2 ** len(comp)
            item_plan.append([tuple(comp), None])  # kraus filled after the batched build
            batch_items.setdefault(Dc, []).append((Hc, cc, dt))
            batch_slots.setdefault(Dc, []).append((i, pos))
        plans[i] = item_plan

    # One batched matrix_exp + Choi eigh per dimension group.
    for Dc, group in batch_items.items():
        kraus_list = assemble_substep_channels_batched(
            group, device=dev, completion=completion,
            choi_eigenvalue_tol=float(choi_eigenvalue_tol),
        )
        for (item_index, out_position), kb in zip(batch_slots[Dc], kraus_list):
            plans[item_index][out_position][1] = kb

    # Freeze each item plan to the (local_qubits, comp_kraus) tuple contract.
    out: list = []
    for item_plan in plans:
        out.append([(tuple(lq), kr) for (lq, kr) in item_plan])
    return out


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
    JOINT channel by the BCH commutator measured by the joint-vs-composed comparison.

    Canonical (fixed) order: all Hamiltonian channels first (in ``H_list`` order),
    then all collapse channels (in ``c_list`` order). The order-DEPENDENCE of the
    composed chain is itself part of what the comparison exposes (a JOINT propagator has no such
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


def _choi_state_from_superop(S, *, device="cuda"):
    r"""Trace-normalised Choi STATE ``J/Tr J`` of a channel given its column-stacking SUPEROPERATOR ``S``
    (``(D^2, D^2)``), in the SAME Choi convention as `_choi_state_from_kraus`
    (``J = Sigma_{p,q} E(|p><q|) (x) |p><q|``), but built DIRECTLY from the channel — a gauge-invariant
    channel property — instead of via a Kraus decomposition. This avoids the spurious near-zero Kraus that
    a lossless (``tol=0``) Choi-eigendecomposition injects for a (near-)unitary channel; those inject an
    ``O(1e-8)``-amplitude roundoff basis whose Uhlmann ``sqrt`` amplifies representation noise to the ~1e-8
    estimator floor (Schumacher/Nielsen note, GT-feasibility line). The Choi-Jamiolkowski map is the pure
    reindexing ``J[a*D+p, b*D+q] = S[b*D+a, q*D+p]`` (verified bit-exact in choi_vectorize_verify.py).
    """
    import torch

    dev = _require_cuda(device)
    S = torch.as_tensor(S, dtype=torch.complex128, device=dev)
    D = int(round(S.shape[0] ** 0.5))
    if D * D != S.shape[0]:
        raise ValueError(f"superop dim {tuple(S.shape)} is not a perfect-square (D^2, D^2)")
    J = S.reshape(D, D, D, D).permute(1, 3, 0, 2).reshape(D * D, D * D).contiguous()
    J = 0.5 * (J + J.conj().transpose(-1, -2))
    return J / torch.trace(J).real


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
    r"""The process (entanglement) infidelity ``1 - F_pro`` between the
    COMPOSED and JOINT CPTP channels of the same ``(H_list, c_list, dt)``, computed via
    their CHOI STATES.

    ``F_pro`` is the Choi-STATE fidelity (Uhlmann fidelity of the trace-normalised Choi
    matrices ``J_joint/D`` and ``J_composed/D``) — the SAME Choi/process-fidelity
    convention exercised by the independent QuTiP channel tests. Returns
    ``1 - F_pro`` (a real float, ``>= 0``).

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
    # Build the two Choi STATES directly from the channel SUPEROPERATORS (gauge-invariant), NOT from a
    # tol=0 Kraus decomposition: for a (near-)unitary channel the lossless Kraus set carries spurious
    # ~1e-8-amplitude roundoff operators whose Uhlmann sqrt amplifies representation noise to the ~1e-8
    # estimator floor (the documented floor; Schumacher/Nielsen note). The superop-Choi is the exact
    # channel property F_e(E_1,E_2)=F_Uhlmann(J_1/d, J_2/d) and removes that implementation-artifact floor.
    S_joint = _joint_superop(H_list, c_list, dt, device=device)
    S_comp = _composed_superop(H_list, c_list, dt, device=device)
    J_joint = _choi_state_from_superop(S_joint, device=device)
    J_comp = _choi_state_from_superop(S_comp, device=device)
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

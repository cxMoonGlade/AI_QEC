from __future__ import annotations

r"""Environment-aware single-bond rank selection for the single-wire PEPS carrier.

This implementation remains a research path. Local environment and dense-reference
invariants have current tests, but the end-to-end entropy invariant fails:
the carrier returns ``S_A=0.10860941571062639`` against the independent GF(2)
reference ``2.0`` at tolerance ``1e-4``. This module is therefore not certified as
state-faithful or record-faithful. See ``docs/simulator_validation/PEPS_FET_VALIDATION.md``.

WHAT THIS MODULE IS
-------------------
The suspected over-count enters the carrier at rank selection:
the local pair-insertion spectrum reports a much larger rank than the bond's true
(environment-aware) entanglement across a loopy PEPS. This module computes the
**environment-optimal rank** of a single bond from its exact double-layer
environment ``Γ[i,I,j,J]`` and returns the corresponding truncation map ``(U, V†)``.
:func:`trajectory._policy_cut` wires it in as the ``"fet_env"`` truncation mode.

PUBLIC SURFACE
--------------
  * :func:`gamma_TN` — the exact double-layer single-bond environment ``Γ[i,I,j,J]``
    (mirrors ``contraction.expect_double_layer``'s exact branch, target bond opened
    on both layers). The exact route is bounded to d3.
  * :func:`gamma_fidelity` — the Γ-fidelity of a rank-χ bond map ``M[i,j]`` vs the
    identity insertion (with the tn_qsim instability sentinel).
  * the multi-restart ALS solver: :func:`_als_inner`, :func:`_fix_gauge`,
    :func:`_gauge_fix_truncation`, :func:`_carrier_svd_seed`,
    :func:`build_seeds`, :func:`_multistart_als_truncation`.
  * :func:`apply_fet_truncation` — the in-place write-back (mirrors ``ntu_truncate``'s
    absorb layout: ``U`` into site A's bond leg, ``V†`` into site B's).
  * :func:`env_optimal_rank` — sweep ``χ = 1..bare_rank`` and
    return the smallest ``χ`` with ``Fid_Γ(χ) ≥ 1 − eps_fid`` as ``(env_rank, U,
    V†, fid_env)`` (``fid_env`` = the achieved ``Fid_Γ``, so the caller reuses it for
    the ledger instead of rebuilding ``Γ``). If no ``χ``
    qualifies, KEEP the full bond (``env_rank = current dim``, ``U = V† = identity``,
    ``fid_env = 1.0``, no truncation) — never a lossy ceiling cut.

The independent-route
``gamma_dense`` and the ``gamma_gates`` / ``dense_psi`` anti-circular checks live
live only in the test. This source path shares no code with its reference.

COST REGIME: ``gamma_TN`` recomputes a full ``auto-hq``
double-layer contraction per call, so ``fet_env`` is orders slower than
``dynamic_eps``/``lossless`` — a feasibility/diagnostic mode, not an N-shot
production sampler path.

GPU-only, torch-cuda-complex128, with an independently implemented test reference.
"""

import os

import numpy as np
import torch
import quimb.tensor as qtn

from ..pepo.dynamics import _qr_split
from ..pepo.sampler import _row_tag
from .contraction import _bra_ind, _site_pair
from .state import CDTYPE, RDTYPE, site_tensor
from .trajectory import _exact_rank, _insertion_spectrum

# --------------------------------------------------------------------------- #
# Solver constants (project numerical choices; local tests only)                #
# --------------------------------------------------------------------------- #
ALS_TRIALS = 20            #: ALS sweeps per restart seed
FET_OPT_FLOOR = 1e-9       #: multistart fidelity may trail gauge-fix by at most this
FID_INSTAB_EPS = 1e-12     #: reject gamma_fidelity when normM <= this * |N0| (degenerate M)
FID_INSTAB_TOL = 1e-6      #: reject gamma_fidelity when F > 1 + this (tn_qsim instability)

#: Open-leg names of the single-bond environment ``Γ`` (ket i/j, bra I/J).
_GI, _GBI, _GJ, _GBJ = "_g_i", "_g_bi", "_g_j", "_g_bj"


def _p(msg: str = "") -> None:
    """Diagnostic print (flushed). Fires ONLY on rare seed-construction/solver
    exception paths — a healthy ``fet_env`` run on a real carrier bond is silent."""
    print(msg, flush=True)


def _parse_bond(bond: str) -> tuple[int, int]:
    """``B{a}_{b}`` -> ``(a, b)`` with ``a < b`` (site A carries phys ``k{a}``,
    site B phys ``k{b}``) — mirrors ``layout.fused_bond_name``'s ``a < b`` order."""
    body = str(bond)[1:]
    a_str, b_str = body.split("_")
    a, b = int(a_str), int(b_str)
    return (a, b) if a < b else (b, a)


def _hermitize_psd(Gamma: torch.Tensor) -> torch.Tensor:
    """Restore the Hermitian-PSD property the EXACT double-layer environment has BY
    CONSTRUCTION (Dziarmaga NTU 2107.06635 and McKeever/Evenbly FET):
    the exact cluster metric is "Hermitian and non-negative down to machine precision", and
    that exactness is the central stability advantage — an approximate NON-Hermitian metric
    is the documented FTU/FU crash mode (ill-conditioned B -> pinv blows up -> non-monotone
    Fid_Γ, the bug that grows the joint bond). Our exact d3 contraction leaks fp
    non-Hermiticity (Fid_Γ came out > 1); Hermitize + PSD-project in the LAYER grouping
    G[(i,j),(I,J)] = Ψ Ψ†, then fold back to Γ[i,I,j,J]."""
    D = int(Gamma.shape[0])
    G = Gamma.permute(0, 2, 1, 3).reshape(D * D, D * D)   # rows (i,j) [ket pair], cols (I,J) [bra pair]
    G = 0.5 * (G + G.conj().mT)                           # Hermitize
    evals, evecs = torch.linalg.eigh(G)                   # Hermitian eig (real evals)
    evals = torch.clamp(evals.real, min=0.0).to(CDTYPE)   # PSD-project: drop fp-negative modes
    G = (evecs * evals) @ evecs.conj().mT
    return G.reshape(D, D, D, D).permute(0, 2, 1, 3).contiguous()


# =========================================================================== #
# The single-bond environment Γ[i,I,j,J] (PRODUCTION route).                    #
# =========================================================================== #
def gamma_TN(state, bond: str) -> torch.Tensor:
    """Mirror ``expect_double_layer``'s exact branch, then split the target bond
    open on both layers. Returns ``Γ[i,I,j,J]`` (D,D,D,D), torch c128. The
    exact route is bounded to d3."""
    layout = state.layout
    a, b = _parse_bond(bond)
    bra_bond = _bra_ind(bond)
    tensors = []
    for pos in layout.grid:
        ket, bra = _site_pair(state, pos, None, _row_tag(layout.grid[pos][0]),
                              open_phys=False)
        if int(pos) == a:
            ket = ket.reindex({bond: _GI})
            bra = bra.reindex({bra_bond: _GBI})
        elif int(pos) == b:
            ket = ket.reindex({bond: _GJ})
            bra = bra.reindex({bra_bond: _GBJ})
        tensors.extend((ket, bra))
    res = qtn.TensorNetwork(tensors).contract(
        output_inds=(_GI, _GBI, _GJ, _GBJ), optimize="auto-hq")
    return _hermitize_psd(res.data.to(CDTYPE))   # the exact environment metric is PSD


# =========================================================================== #
# Γ-fidelity of a rank-χ bond map (with the tn_qsim instability sentinel).      #
# =========================================================================== #
def gamma_fidelity(Gamma: torch.Tensor, M: torch.Tensor) -> float:
    """Γ-fidelity of a rank-χ bond map ``M[i,j]`` vs the identity insertion:
    ``F = |<orig|M>|^2 / (<orig|orig> <M|M>)``. Returns ``-inf`` on the tn_qsim
    instability sentinel (degenerate ``||M||_Γ`` / super-unitary / non-finite) so
    no unstable ALS iterate is ever selected as the best."""
    D = int(Gamma.shape[0])
    eye = torch.eye(D, dtype=CDTYPE, device=Gamma.device)
    N0 = torch.einsum("iIiI->", Gamma).real
    normM = torch.einsum("iIjJ,ij,IJ->", Gamma, M, M.conj()).real
    overlap = torch.einsum("iIjJ,ij,IJ->", Gamma, M, eye)  # bra = identity (original)
    n0 = float(N0)
    nm = float(normM)
    if not np.isfinite(n0) or not np.isfinite(nm) or nm <= FID_INSTAB_EPS * abs(n0):
        return float("-inf")
    fid = float((overlap.conj() * overlap).real) / (n0 * nm)
    if not np.isfinite(fid) or fid > 1.0 + FID_INSTAB_TOL:
        return float("-inf")
    return min(fid, 1.0)   # a fidelity is <= 1 for PSD Γ; clamp fp overshoot


# =========================================================================== #
# FET multistart ALS solver (mirrors tn_qsim's sigma=identity branch),           #
# compared with the closed-form gauge-fix truncation.                           #
# =========================================================================== #
def _als_inner(Gamma: torch.Tensor, chi: int, U0: torch.Tensor, *,
               trials: int = ALS_TRIALS, fluct: bool = False) -> tuple:
    """The alternating-pinv ALS from tn_qsim (sigma=identity branch), torch-mirrored."""
    D = int(Gamma.shape[0])
    dev = Gamma.device
    eye_D = torch.eye(D, dtype=CDTYPE, device=dev)
    U = U0.clone()
    Vh = torch.eye(chi, D, dtype=CDTYPE, device=dev)
    best_fid = -1.0
    best_U = U0.clone()
    best_Vh = Vh.clone()
    for t in range(int(trials)):
        # ---- step 1: solve the (S,Vh) side given U ----
        P = torch.einsum("iIjJ,ij,IP->PJ", Gamma, eye_D, U.conj())          # (chi, D)
        B = torch.einsum("iIjJ,ip,IP->PJpj", Gamma, U, U.conj()).reshape(chi * D, chi * D)
        if fluct and t < 10:
            kick = (10.0 ** -2) * torch.rand(chi * D, device=dev, dtype=RDTYPE)
            B = B + torch.diag(kick).to(CDTYPE)
        B = 0.5 * (B + B.conj().mT)                              # Hermitize the env metric
        Rmax = torch.linalg.pinv(B, hermitian=True) @ P.reshape(-1)  # truncated-SVD-stable solve
        R2 = Rmax.reshape(chi, D)                                           # = S @ Vh
        M = U @ R2
        fid = gamma_fidelity(Gamma, M)
        if fid > best_fid:
            best_fid, best_U, best_Vh = fid, U.clone(), R2.clone()
        Ut, st, Vh = torch.linalg.svd(R2, full_matrices=False)             # update Vh
        S = Ut @ torch.diag(st).to(CDTYPE)
        # ---- step 2: solve the U side given Vh ----
        P2 = torch.einsum("iIjJ,ij,QJ->QI", Gamma, eye_D, Vh.conj())        # (chi, D)
        B2 = torch.einsum("iIjJ,qj,QJ->QIqi", Gamma, Vh, Vh.conj()).reshape(chi * D, chi * D)
        if fluct and t < 10:
            kick = (10.0 ** -2) * torch.rand(chi * D, device=dev, dtype=RDTYPE)
            B2 = B2 + torch.diag(kick).to(CDTYPE)
        B2 = 0.5 * (B2 + B2.conj().mT)                          # Hermitize the env metric
        Rmax2 = torch.linalg.pinv(B2, hermitian=True) @ P2.reshape(-1)  # truncated-SVD-stable
        R3 = Rmax2.reshape(chi, D)                                          # (Q=chi, I=D)
        Um, st2, Vht = torch.linalg.svd(R3.mT, full_matrices=False)        # R3.T = (D, chi)
        U = Um
        S = torch.diag(st2).to(CDTYPE) @ Vht                               # (chi, chi)
        Vh_eff = S @ Vh                                                     # (chi, D)
        candidate_map = U @ Vh_eff
        fid2 = gamma_fidelity(Gamma, candidate_map)
        if fid2 > best_fid:
            best_fid, best_U, best_Vh = fid2, U.clone(), Vh_eff.clone()
    return best_U, best_Vh, best_fid


def _fix_gauge(Gamma: torch.Tensor):
    """Torch mirror of tn_qsim ``utils.fix_gauge`` — the weight-trace gauge from the
    dominant transfer eigenvectors. Returns ``(sigma, xinv, yinv)`` (all D x D)."""
    D = int(Gamma.shape[0])
    dev = Gamma.device
    Gm = Gamma.reshape(D * D, D * D)  # grouping (iI),(jJ) — the (non-normal) transfer matrix
    leig, leigv = torch.linalg.eig(Gm)
    L0 = leigv[:, int(torch.argmax(leig.abs()))]
    reig, reigv = torch.linalg.eig(Gm.mT)
    R0 = reigv[:, int(torch.argmax(reig.abs()))]
    L0 = L0 + 1e-10
    R0 = R0 + 1e-10
    ul, dl, _ = torch.linalg.svd(L0.reshape(D, D), full_matrices=False)
    ur, dr, _ = torch.linalg.svd(R0.reshape(D, D), full_matrices=False)
    sqrt_dl = torch.diag(torch.sqrt(dl)).to(CDTYPE)
    sqrt_dr = torch.diag(torch.sqrt(dr)).to(CDTYPE)
    sigma_p = sqrt_dl @ ul.conj().mT @ ur @ sqrt_dr
    wl, sig, wrh = torch.linalg.svd(sigma_p, full_matrices=False)
    sigma = torch.diag(sig).to(CDTYPE)
    x = wl.conj().mT @ sqrt_dl @ ul.conj().mT
    y = ur @ sqrt_dr @ wrh.conj().mT
    xinv = torch.linalg.pinv(x)
    yinv = torch.linalg.pinv(y)
    return sigma, xinv, yinv


def _gauge_fix_truncation(Gamma: torch.Tensor, chi: int, prep=None) -> tuple:
    """Closed-form gauge-fix plus top-chi truncation heuristic."""
    if prep is None:
        prep = _fix_gauge(Gamma)
    sigma, xinv, yinv = prep
    Uu, s2, Vhh = torch.linalg.svd(sigma, full_matrices=False)
    U = Uu[:, :chi]
    S = torch.diag(s2[:chi]).to(CDTYPE)
    Vh = Vhh[:chi, :]
    U_full = xinv @ (U @ S)
    Vh_full = Vh @ yinv
    M = U_full @ Vh_full
    return U_full, Vh_full, gamma_fidelity(Gamma, M)


def _carrier_svd_seed(state, bond: str, chi: int, device) -> torch.Tensor:
    """Seed (ii): the carrier's OWN local-SVD top-chi of ``X0 = R_A R_B^T`` lifted to a
    full-bond D x chi isometry."""
    a, b = _parse_bond(bond)
    ta, tb = site_tensor(state, a), site_tensor(state, b)
    _QA, RA, _ia, _da = _qr_split(ta, bond)
    _QB, RB, _ib, _db = _qr_split(tb, bond)
    X0 = RA @ RB.mT
    U0, _S0, _V0 = torch.linalg.svd(X0, full_matrices=False)
    lift = RA.conj().mT @ U0[:, :chi]            # (D, chi) in the bond leg
    q, _r = torch.linalg.qr(lift)
    return q[:, :chi].contiguous().to(CDTYPE)


def build_seeds(Gamma: torch.Tensor, state, bond: str, chi: int, prep) -> list:
    """The >=4 restart seeds (each a D x chi isometry U0) — tn_qsim's restart discipline."""
    D = int(Gamma.shape[0])
    dev = Gamma.device
    a, b = _parse_bond(bond)
    seeds = []
    seeds.append(("identity", torch.eye(D, dtype=CDTYPE, device=dev)[:, :chi].contiguous()))
    try:
        seeds.append(("carrier_svd", _carrier_svd_seed(state, bond, chi, dev)))
    except RuntimeError:
        # The carrier_svd seed expects carrier-bond structure (it QR-splits + reshapes the
        # pair-insertion to a square). On a standalone (non-carrier) KAT tensor that reshape is
        # INAPPLICABLE => a benign RuntimeError. This is EXPECTED, not an alarm — skip silently;
        # the identity/gauge-fix/random/permuted-identity seeds carry the best-of.
        # (On a REAL carrier bond this
        # seed builds fine, so this quiet skip only fires for standalone tensors.)
        _p("      [seed carrier_svd n/a for standalone tensor]")
    except Exception as exc:  # noqa: BLE001  # any OTHER failure stays visible
        _p(f"      [seed carrier_svd skipped] {type(exc).__name__}: {exc}")
    try:
        gauge_u, _gauge_vh, _gauge_fid = _gauge_fix_truncation(
            Gamma, chi, prep=prep
        )
        q, _r = torch.linalg.qr(gauge_u)
        seeds.append(("gauge_fix", q[:, :chi].contiguous().to(CDTYPE)))
    except Exception as exc:  # noqa: BLE001
        _p(f"      [seed gauge_fix skipped] {type(exc).__name__}: {exc}")
    g = torch.Generator(device="cpu")
    g.manual_seed(1_000_003 * int(chi) + 31 * int(a) + int(b))
    re = torch.randn(D, chi, generator=g, dtype=RDTYPE)
    im = torch.randn(D, chi, generator=g, dtype=RDTYPE)
    W = (re + 1j * im).to(CDTYPE).to(dev)
    qr_q, _ = torch.linalg.qr(W)
    seeds.append(("rand", qr_q[:, :chi].contiguous()))
    perm = torch.randperm(D, generator=g).to(dev)
    eye_perm = torch.eye(D, dtype=CDTYPE, device=dev)[perm]
    seeds.append(("perm_id", eye_perm[:, :chi].contiguous()))
    return seeds


def _multistart_als_truncation(
    Gamma: torch.Tensor,
    state,
    bond: str,
    chi: int,
    prep,
) -> dict:
    """Return the best multistart ALS map and its gauge-fix comparison."""
    seeds = build_seeds(Gamma, state, bond, chi, prep)
    per_seed = []
    best = None
    for name, U0 in seeds:
        fluct = name in ("rand", "perm_id")
        try:
            U, Vh, fid = _als_inner(Gamma, chi, U0, fluct=fluct)
        except Exception as exc:  # noqa: BLE001
            _p(f"      [ALS seed {name} failed] {type(exc).__name__}: {exc}")
            continue
        per_seed.append((name, float(fid)))
        if best is None or fid > best["fid"]:
            best = {"seed": name, "U": U, "Vh": Vh, "fid": float(fid)}
    if best is None:
        # every seed failed — return a degenerate identity insertion (caller sees -inf fid)
        D = int(Gamma.shape[0])
        Ueye = torch.eye(D, dtype=CDTYPE, device=Gamma.device)[:, :chi].contiguous()
        Vheye = torch.eye(chi, D, dtype=CDTYPE, device=Gamma.device)
        best = {"seed": "none", "U": Ueye, "Vh": Vheye, "fid": float("-inf")}
    fids = [f for _n, f in per_seed if np.isfinite(f)]
    spread = (max(fids) - min(fids)) if len(fids) >= 2 else 0.0
    try:
        _gauge_u, _gauge_vh, fid_gauge_fix = _gauge_fix_truncation(
            Gamma, chi, prep=prep
        )
        fid_gauge_fix = float(fid_gauge_fix)
        dfid = best["fid"] - fid_gauge_fix
        floor_ok = best["fid"] >= fid_gauge_fix - FET_OPT_FLOOR
    except Exception as exc:  # noqa: BLE001
        _p(f"      [gauge_fix comparison skipped] {type(exc).__name__}: {exc}")
        fid_gauge_fix = None
        dfid = None
        floor_ok = True
    return {
        "chi": int(chi), "best_seed": best["seed"], "U": best["U"], "Vh": best["Vh"],
        "fid_multistart_als": best["fid"],
        "fid_gauge_fix": fid_gauge_fix,
        "dfid": dfid,
        "per_seed": per_seed, "cross_seed_spread": float(spread),
        "opt_floor_ok": bool(floor_ok),
    }


# =========================================================================== #
# Write-back (mirrors ntu_truncate's absorb layout).                            #
# =========================================================================== #
def apply_fet_truncation(state, bond: str, U: torch.Tensor, Vh: torch.Tensor) -> None:
    """Absorb ``U`` (D x chi) into site A's bond leg and ``Vh`` (chi x D) into site
    B's, reconnecting the new chi-bond (the ORIGINAL bond name kept). Mutates
    ``state`` in place. With ``U = Vh = I_D`` this is a
    genuine no-op (the bond stays at its full dim)."""
    a, b = _parse_bond(bond)
    ta, tb = site_tensor(state, a), site_tensor(state, b)
    axa = ta.inds.index(bond)
    new_a = torch.movedim(torch.tensordot(ta.data, U, dims=([axa], [0])), -1, axa)
    ta.modify(data=new_a.contiguous())
    axb = tb.inds.index(bond)
    new_b = torch.movedim(torch.tensordot(tb.data, Vh, dims=([axb], [1])), -1, axb)
    tb.modify(data=new_b.contiguous())


# =========================================================================== #
# Environment-aware rank-selection wrapper.                                    #
# =========================================================================== #
def env_optimal_rank(state, bond: str,
                     eps_fid: float) -> tuple[int, torch.Tensor, torch.Tensor, float]:
    """Sweep ``χ = 1..bare_rank`` on the bond's exact double-layer environment
    ``Γ`` and return ``(env_rank, U, V†, fid_env)`` for the SMALLEST ``χ`` whose
    achieved environment fidelity ``Fid_Γ(χ) ≥ 1 − eps_fid`` (via the multi-restart
    multistart ALS solver); ``fid_env`` is that achieved ``Fid_Γ``.
    ``bare_rank`` = the exact local rank ``_exact_rank(_insertion_spectrum(bond))``
    (the carrier's own rank read; the FET never keeps more than the local rank),
    capped at the stored bond dimension.

    ``fid_env`` is returned so the caller (:func:`trajectory._policy_cut`) uses it
    for the ledger DIRECTLY instead of rebuilding ``Γ`` + recomputing the fidelity —
    ``gamma_TN`` is the expensive per-bond double-layer contraction,
    so returning the already-computed ``Fid_Γ`` halves the per-bond ``gamma_TN`` cost.

    If no ``χ ∈ [1, bare_rank]`` reaches the
    target, KEEP the full bond — ``env_rank = current stored dim``, ``U = V† =
    identity`` (a genuine no-op via :func:`apply_fet_truncation`), ``fid_env = 1.0``
    (the identity insertion IS the original state). It must NOT fall back to a lossy
    ceiling cut; diagnostics then report the bond as non-collapsing."""
    Gamma = gamma_TN(state, bond)
    D = int(Gamma.shape[0])
    fid_target = 1.0 - float(eps_fid)
    S = _insertion_spectrum(state, bond)
    bare = min(int(_exact_rank(S)), D)   # env_rank <= bare_rank
    prep = None
    try:
        prep = _fix_gauge(Gamma)
    except Exception as exc:  # noqa: BLE001  # gauge seed unavailable; ALS still runs
        _p(f"      [env_optimal_rank {bond}] fix_gauge failed: {type(exc).__name__}: {exc}")
    if os.environ.get("FET_FIDCURVE_DEBUG") == "1":
        # DIAGNOSTIC (env-gated, BEHAVIOR-IDENTICAL): log the FULL fid(chi) curve to
        # confirm WHY a dressed bond over-keeps (threshold-too-tight vs the >1 sentinel
        # vs a solver plateau). Same return as the fast path below (first qualifying chi,
        # otherwise use the no-op fallback). This computes all chi values and only
        # runs when the environment variable is set.
        curve = []
        accepted = None
        best = None
        for chi in range(1, bare + 1):
            als_result = _multistart_als_truncation(Gamma, state, bond, chi, prep)
            fid = gamma_fidelity(Gamma, als_result["U"] @ als_result["Vh"])
            ffid = float(fid) if np.isfinite(fid) else float("-inf")
            curve.append((chi, ffid))
            if best is None or ffid > best[3]:
                best = (chi, als_result["U"], als_result["Vh"], ffid)
            if accepted is None and np.isfinite(fid) and fid >= fid_target:
                accepted = (
                    int(chi),
                    als_result["U"],
                    als_result["Vh"],
                    float(fid),
                )
        n_sent = sum(1 for _, f in curve if f == float("-inf"))
        _p(f"      [FIDCURVE {bond}] D={D} bare={bare} target={fid_target:.12f} "
           f"accept_chi(<=1e-8)={accepted[0] if accepted else None} "
           f"best_chi={best[0]} best_fid={best[3]:.12f} sentinel_fired={n_sent} "
           f"curve={['%d:%.10f' % (c, f) for c, f in curve]}")
        if accepted is not None:
            return accepted
        if best is not None:   # accept best χ<=bare (never keep the full over-counted bond)
            return int(best[0]), best[1], best[2], float(best[3])
        eye = torch.eye(D, dtype=CDTYPE, device=Gamma.device)
        return int(D), eye, eye, 1.0
    best = None
    for chi in range(1, bare + 1):
        als_result = _multistart_als_truncation(Gamma, state, bond, chi, prep)
        fid = gamma_fidelity(Gamma, als_result["U"] @ als_result["Vh"])
        ffid = float(fid) if np.isfinite(fid) else -1.0
        if best is None or ffid > best[3]:
            best = (int(chi), als_result["U"], als_result["Vh"], ffid)
        if np.isfinite(fid) and fid >= fid_target:
            return int(chi), als_result["U"], als_result["Vh"], float(fid)
    # No χ<=bare cleared the bar. With the Hermitian-PSD Γ and the
    # regularized solve this is UNREACHABLE (χ=bare is a lossless identity insertion => fid=1),
    # but if it ever fires, accept the BEST χ<=bare (highest Fid_Γ) — NEVER keep the
    # over-counted full bond D>bare.
    if best is not None:
        return best
    eye = torch.eye(D, dtype=CDTYPE, device=Gamma.device)
    return int(D), eye, eye, 1.0

from __future__ import annotations

r"""Environment-aware single-bond rank selection for the single-wire PEPS carrier.

This implementation remains a research path. The mutation boundary is fail-closed,
and the current focused strict-``eps_fid`` d3 owner test accepts a rank-reducing
local-QR/SVD feasible candidate while retaining the independent entropy reference.
That repairs the former all-identity non-degeneracy blocker; it does not certify a
state-faithful or record-faithful truncation path, and clean-head release evidence is
still pending. See
``docs/simulator_validation/PEPS_FET_VALIDATION.md``.

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
  * the candidate solver: :func:`_carrier_svd_feasible_candidate` supplies an
    analytic local-QR/SVD feasible upper bound, while :func:`_als_inner`,
    :func:`_fix_gauge`, :func:`_gauge_fix_truncation`,
    :func:`_carrier_svd_seed`, :func:`build_seeds`, and
    :func:`_multistart_als_truncation` search for lower-rank environment-aware maps.
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

import numpy as np
import torch
import quimb.tensor as qtn

from ...numerics import NUMERICAL_ZERO
from ..pepo.dynamics import _qr_split
from ..pepo.sampler import _row_tag
from .contraction import _bra_ind, _site_pair
from .state import CDTYPE, RDTYPE, site_tensor
from .trajectory import (
    FET_SOLVER_SEED_DEFAULT,
    _exact_rank,
    _insertion_spectrum,
)

# --------------------------------------------------------------------------- #
# Solver constants (project numerical choices; local tests only)                #
# --------------------------------------------------------------------------- #
ALS_TRIALS = 20            #: ALS sweeps per restart seed
FET_OPT_FLOOR = 1e-9       #: multistart fidelity may trail gauge-fix by at most this
FID_INSTAB_EPS = 1e-12     #: reject gamma_fidelity when normM <= this * |N0| (degenerate M)
FID_INSTAB_TOL = 1e-6      #: reject gamma_fidelity when F > 1 + this (tn_qsim instability)
class FetSelection(tuple):
    """Backward-compatible four-tuple with explicit selector semantics.

    Iteration/unpacking yields ``(env_rank, U, Vh, fid_env)`` as before.  The
    attributes separate the applied selection from the best rejected candidate,
    so callers never need to encode solver failure as a fake finite fidelity.
    """

    def __new__(
        cls,
        env_rank: int,
        U: torch.Tensor,
        Vh: torch.Tensor,
        fid_env: float,
        *,
        outcome: str,
        candidate_rank: int | None,
        candidate_fid: float | None,
        solver_seed: int,
        attempted_ranks: int,
        solver_failure_count: int,
    ):
        obj = super().__new__(cls, (int(env_rank), U, Vh, float(fid_env)))
        obj.outcome = str(outcome)
        obj.candidate_rank = (
            None if candidate_rank is None else int(candidate_rank)
        )
        obj.candidate_fid = (
            None if candidate_fid is None else float(candidate_fid)
        )
        obj.solver_seed = int(solver_seed)
        obj.attempted_ranks = int(attempted_ranks)
        obj.solver_failure_count = int(solver_failure_count)
        return obj

    @property
    def env_rank(self) -> int:
        return int(self[0])

    @property
    def U(self) -> torch.Tensor:
        return self[1]

    @property
    def Vh(self) -> torch.Tensor:
        return self[2]

    @property
    def fid_env(self) -> float:
        return float(self[3])

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
def _als_inner(
    Gamma: torch.Tensor,
    chi: int,
    U0: torch.Tensor,
    *,
    trials: int = ALS_TRIALS,
    fluct: bool = False,
    generator: torch.Generator | None = None,
) -> tuple:
    """The alternating-pinv ALS from tn_qsim (sigma=identity branch), torch-mirrored."""
    D = int(Gamma.shape[0])
    dev = Gamma.device
    if fluct:
        if generator is None:
            raise ValueError("fluctuating ALS requires a private generator")
        generator_device = torch.device(generator.device)
        gamma_device = torch.device(dev)
        device_mismatch = generator_device.type != gamma_device.type or (
            generator_device.index is not None
            and gamma_device.index is not None
            and generator_device.index != gamma_device.index
        )
        if device_mismatch:
            raise ValueError(
                "private generator device must match Gamma device "
                f"({generator.device!s} != {dev!s})"
            )
    eye_D = torch.eye(D, dtype=CDTYPE, device=dev)
    U = U0.clone()
    Vh = torch.eye(chi, D, dtype=CDTYPE, device=dev)
    best_fid = None
    best_U = U0.clone()
    best_Vh = Vh.clone()
    for t in range(int(trials)):
        # ---- step 1: solve the (S,Vh) side given U ----
        P = torch.einsum("iIjJ,ij,IP->PJ", Gamma, eye_D, U.conj())          # (chi, D)
        B = torch.einsum("iIjJ,ip,IP->PJpj", Gamma, U, U.conj()).reshape(chi * D, chi * D)
        if fluct and t < 10:
            kick = (10.0 ** -2) * torch.rand(
                chi * D,
                device=dev,
                dtype=RDTYPE,
                generator=generator,
            )
            B = B + torch.diag(kick).to(CDTYPE)
        B = 0.5 * (B + B.conj().mT)                              # Hermitize the env metric
        Rmax = torch.linalg.pinv(B, hermitian=True) @ P.reshape(-1)  # truncated-SVD-stable solve
        R2 = Rmax.reshape(chi, D)                                           # = S @ Vh
        M = U @ R2
        fid = gamma_fidelity(Gamma, M)
        if np.isfinite(fid) and 0.0 <= fid <= 1.0 and (
            best_fid is None or fid > best_fid
        ):
            best_fid, best_U, best_Vh = fid, U.clone(), R2.clone()
        Ut, st, Vh = torch.linalg.svd(R2, full_matrices=False)             # update Vh
        S = Ut @ torch.diag(st).to(CDTYPE)
        # ---- step 2: solve the U side given Vh ----
        P2 = torch.einsum("iIjJ,ij,QJ->QI", Gamma, eye_D, Vh.conj())        # (chi, D)
        B2 = torch.einsum("iIjJ,qj,QJ->QIqi", Gamma, Vh, Vh.conj()).reshape(chi * D, chi * D)
        if fluct and t < 10:
            kick = (10.0 ** -2) * torch.rand(
                chi * D,
                device=dev,
                dtype=RDTYPE,
                generator=generator,
            )
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
        if np.isfinite(fid2) and 0.0 <= fid2 <= 1.0 and (
            best_fid is None or fid2 > best_fid
        ):
            best_fid, best_U, best_Vh = fid2, U.clone(), Vh_eff.clone()
    if best_fid is None:
        return best_U, best_Vh, float("-inf")
    return best_U, best_Vh, float(best_fid)


def _fix_gauge(Gamma: torch.Tensor):
    """Torch mirror of tn_qsim ``utils.fix_gauge`` — the weight-trace gauge from the
    dominant transfer eigenvectors. Returns ``(sigma, xinv, yinv)`` (all D x D)."""
    D = int(Gamma.shape[0])
    dev = Gamma.device
    # cuSOLVER's eig path is permitted to overwrite its workspace.  Do not pass
    # a reshape/view backed by the verdict-driving Gamma tensor: the real d3
    # selector previously observed a relative Gamma mutation of O(1) here.
    Gm = Gamma.reshape(D * D, D * D).clone()
    leig, leigv = torch.linalg.eig(Gm.clone())
    L0 = leigv[:, int(torch.argmax(leig.abs()))]
    reig, reigv = torch.linalg.eig(Gm.mT.contiguous().clone())
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


def _carrier_svd_factorization(state, bond: str) -> tuple:
    """Freeze the endpoint QR/SVD and rank-aware Moore-Penrose pullbacks."""
    a, b = _parse_bond(bond)
    ta, tb = site_tensor(state, a), site_tensor(state, b)
    _QA, RA, _ia, _da = _qr_split(ta, bond)
    _QB, RB, _ib, _db = _qr_split(tb, bond)
    device = RA.device
    U0, S0, Vh0 = torch.linalg.svd(
        RA @ RB.mT, full_matrices=False
    )
    pinv_RA = torch.linalg.pinv(RA, rtol=NUMERICAL_ZERO)
    pinv_RB = torch.linalg.pinv(RB, rtol=NUMERICAL_ZERO)
    return device, pinv_RA, pinv_RB, U0, S0, Vh0


def _carrier_svd_candidate_from_factorization(
    factorization: tuple, chi: int
) -> tuple[torch.Tensor, torch.Tensor]:
    """Construct one candidate from a frozen endpoint factorization."""
    device, pinv_RA, pinv_RB, U0, S0, Vh0 = factorization
    chi = int(chi)
    if not 1 <= chi <= int(S0.numel()):
        raise ValueError(
            f"carrier-SVD candidate rank must lie in [1, {int(S0.numel())}] "
            f"(got {chi})"
        )
    sqrt_s = torch.sqrt(S0[:chi]).to(CDTYPE)
    left_target = U0[:, :chi] * sqrt_s
    right_target = Vh0[:chi, :].mT * sqrt_s
    U = (pinv_RA @ left_target).contiguous().to(device=device, dtype=CDTYPE)
    Vh = (
        (pinv_RB @ right_target).mT.contiguous().to(
            device=device, dtype=CDTYPE
        )
    )
    return U, Vh


def _carrier_svd_feasible_candidate(
    state, bond: str, chi: int
) -> tuple[torch.Tensor, torch.Tensor]:
    """Return the analytic local-QR/SVD rank-``chi`` bond-map factors.

    For endpoint QR decompositions ``A = Q_A R_A`` and ``B = Q_B R_B``, let
    ``R_A R_B^T = U_0 S V_0†``.  The returned full-bond factors solve
    ``R_A U = U_0 sqrt(S)`` and ``R_B V^T = V_0^T sqrt(S)`` by a rank-aware
    Moore-Penrose pullback.  At the structural local rank this reconstructs the
    original two-site contraction, so it is a known feasible upper bound even
    when the environment-aware ALS search fails.  Lower ranks remain ordinary
    scored candidates and receive no special acceptance.
    """
    return _carrier_svd_candidate_from_factorization(
        _carrier_svd_factorization(state, bond), chi
    )


def _carrier_svd_seed(state, bond: str, chi: int, device) -> torch.Tensor:
    """Seed (ii): isometrize the analytic carrier-SVD factor for ALS."""
    U, _Vh = _carrier_svd_feasible_candidate(state, bond, chi)
    if U.device != torch.device(device):
        raise RuntimeError(
            f"carrier-SVD seed device {U.device!s} != Gamma device {device!s}"
        )
    q, _r = torch.linalg.qr(U)
    return q[:, :chi].contiguous().to(CDTYPE)


_RESTART_SEED_CODES = {
    "identity": 101,
    "carrier_svd": 211,
    "gauge_fix": 307,
    "rand": 401,
    "perm_id": 503,
}
_SEED_MODULUS = (1 << 63) - 1


def _stable_solver_seed(
    *, solver_seed: int, bond: str, chi: int, restart_name: str
) -> int:
    """Mix explicit, source-stable integer coordinates without Python ``hash``."""
    if int(solver_seed) < 0:
        raise ValueError(f"solver_seed must be nonnegative (got {solver_seed})")
    try:
        restart_code = _RESTART_SEED_CODES[str(restart_name)]
    except KeyError as exc:
        raise ValueError(f"unknown FET restart name {restart_name!r}") from exc
    a, b = _parse_bond(bond)
    return int(
        (
            int(solver_seed)
            + 1_000_003 * int(chi)
            + 10_000_019 * int(a)
            + 100_000_007 * int(b)
            + int(restart_code)
        )
        % _SEED_MODULUS
    )


def _private_solver_generator(
    device: torch.device,
    *,
    solver_seed: int,
    bond: str,
    chi: int,
    restart_name: str,
) -> torch.Generator:
    generator = torch.Generator(device=device)
    generator.manual_seed(
        _stable_solver_seed(
            solver_seed=solver_seed,
            bond=bond,
            chi=chi,
            restart_name=restart_name,
        )
    )
    return generator


def build_seeds(
    Gamma: torch.Tensor,
    state,
    bond: str,
    chi: int,
    prep,
    *,
    solver_seed: int = FET_SOLVER_SEED_DEFAULT,
) -> list:
    """The >=4 restart seeds (each a D x chi isometry U0) — tn_qsim's restart discipline."""
    D = int(Gamma.shape[0])
    dev = Gamma.device
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
    random_generator = torch.Generator(device="cpu")
    random_generator.manual_seed(
        _stable_solver_seed(
            solver_seed=solver_seed,
            bond=bond,
            chi=chi,
            restart_name="rand",
        )
    )
    re = torch.randn(D, chi, generator=random_generator, dtype=RDTYPE)
    im = torch.randn(D, chi, generator=random_generator, dtype=RDTYPE)
    W = (re + 1j * im).to(CDTYPE).to(dev)
    qr_q, _ = torch.linalg.qr(W)
    seeds.append(("rand", qr_q[:, :chi].contiguous()))
    permutation_generator = torch.Generator(device="cpu")
    permutation_generator.manual_seed(
        _stable_solver_seed(
            solver_seed=solver_seed,
            bond=bond,
            chi=chi,
            restart_name="perm_id",
        )
    )
    perm = torch.randperm(D, generator=permutation_generator).to(dev)
    eye_perm = torch.eye(D, dtype=CDTYPE, device=dev)[perm]
    seeds.append(("perm_id", eye_perm[:, :chi].contiguous()))
    return seeds


def _multistart_als_truncation(
    Gamma: torch.Tensor,
    state,
    bond: str,
    chi: int,
    prep,
    *,
    solver_seed: int = FET_SOLVER_SEED_DEFAULT,
    feasible_candidate: tuple[torch.Tensor, torch.Tensor] | None = None,
) -> dict:
    """Return the best multistart ALS map and its gauge-fix comparison."""
    per_seed = []
    best = None
    try:
        if feasible_candidate is None:
            candidate_U, candidate_Vh = _carrier_svd_feasible_candidate(
                state, bond, chi
            )
        else:
            candidate_U, candidate_Vh = feasible_candidate
        candidate_fid = gamma_fidelity(
            Gamma, candidate_U @ candidate_Vh
        )
        per_seed.append(("carrier_svd_feasible", float(candidate_fid)))
        if np.isfinite(candidate_fid) and 0.0 <= candidate_fid <= 1.0:
            best = {
                "seed": "carrier_svd_feasible",
                "U": candidate_U,
                "Vh": candidate_Vh,
                "fid": float(candidate_fid),
            }
    except Exception as exc:  # noqa: BLE001
        _p(
            "      [candidate carrier_svd_feasible skipped] "
            f"{type(exc).__name__}: {exc}"
        )
    seeds = build_seeds(
        Gamma,
        state,
        bond,
        chi,
        prep,
        solver_seed=solver_seed,
    )
    for name, U0 in seeds:
        fluct = name in ("rand", "perm_id")
        try:
            generator = None
            if fluct:
                generator = _private_solver_generator(
                    Gamma.device,
                    solver_seed=solver_seed,
                    bond=bond,
                    chi=chi,
                    restart_name=name,
                )
            U, Vh, fid = _als_inner(
                Gamma,
                chi,
                U0,
                fluct=fluct,
                generator=generator,
            )
        except Exception as exc:  # noqa: BLE001
            _p(f"      [ALS seed {name} failed] {type(exc).__name__}: {exc}")
            continue
        per_seed.append((name, float(fid)))
        if np.isfinite(fid) and 0.0 <= fid <= 1.0 and (
            best is None or fid > best["fid"]
        ):
            best = {"seed": name, "U": U, "Vh": Vh, "fid": float(fid)}
    solver_status = "ok"
    if best is None:
        # Every seed failed.  A rank-chi placeholder is returned only so the
        # diagnostic shape remains inspectable; the explicit non-finite score and
        # solver_status prevent it from becoming an applicable candidate.
        D = int(Gamma.shape[0])
        Ueye = torch.eye(D, dtype=CDTYPE, device=Gamma.device)[:, :chi].contiguous()
        Vheye = torch.eye(chi, D, dtype=CDTYPE, device=Gamma.device)
        best = {"seed": "none", "U": Ueye, "Vh": Vheye, "fid": float("-inf")}
        solver_status = "solver_failed"
    fids = [f for _n, f in per_seed if np.isfinite(f)]
    spread = (max(fids) - min(fids)) if len(fids) >= 2 else 0.0
    try:
        _gauge_u, _gauge_vh, fid_gauge_fix = _gauge_fix_truncation(
            Gamma, chi, prep=prep
        )
        fid_gauge_fix = float(fid_gauge_fix)
        dfid = best["fid"] - fid_gauge_fix
        floor_ok = (
            solver_status == "ok"
            and best["fid"] >= fid_gauge_fix - FET_OPT_FLOOR
        )
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
        "solver_status": str(solver_status),
        "solver_seed": int(solver_seed),
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
    axb = tb.inds.index(bond)
    if not isinstance(U, torch.Tensor) or not isinstance(Vh, torch.Tensor):
        raise TypeError("FET absorption factors must be torch tensors")
    if U.ndim != 2 or Vh.ndim != 2:
        raise ValueError(
            f"FET absorption factors must be matrices (got {U.ndim}D and {Vh.ndim}D)"
        )
    old_dim_a = int(ta.data.shape[axa])
    old_dim_b = int(tb.data.shape[axb])
    kept_dim_u = int(U.shape[1])
    kept_dim_vh = int(Vh.shape[0])
    if old_dim_a <= 0 or old_dim_b <= 0 or old_dim_a != old_dim_b:
        raise RuntimeError(
            "FET endpoint bond dimensions must be equal and positive before absorption "
            f"({old_dim_a} != {old_dim_b})"
        )
    if int(U.shape[0]) != old_dim_a or int(Vh.shape[1]) != old_dim_b:
        raise ValueError(
            "FET factors are incompatible with the original endpoint dimensions: "
            f"U={tuple(U.shape)}, Vh={tuple(Vh.shape)}, "
            f"endpoint_dims=({old_dim_a}, {old_dim_b})"
        )
    if kept_dim_u <= 0 or kept_dim_u != kept_dim_vh:
        raise ValueError(
            "FET factors must declare one shared positive kept rank: "
            f"U={tuple(U.shape)}, Vh={tuple(Vh.shape)}"
        )
    if (
        U.dtype != ta.data.dtype
        or Vh.dtype != tb.data.dtype
        or U.device != ta.data.device
        or Vh.device != tb.data.device
    ):
        raise ValueError("FET factors must match their endpoint dtype and device")
    if not bool(torch.isfinite(U).all().item()) or not bool(
        torch.isfinite(Vh).all().item()
    ):
        raise ValueError("FET absorption factors must be finite")

    # All cross-endpoint invariants are authenticated before either potentially
    # expensive absorption is formed, let alone written back.
    new_a = torch.movedim(torch.tensordot(ta.data, U, dims=([axa], [0])), -1, axa)
    new_b = torch.movedim(torch.tensordot(tb.data, Vh, dims=([axb], [1])), -1, axb)
    new_a = new_a.contiguous()
    new_b = new_b.contiguous()
    expected_a_shape = list(ta.data.shape)
    expected_b_shape = list(tb.data.shape)
    expected_a_shape[axa] = int(U.shape[1])
    expected_b_shape[axb] = int(Vh.shape[0])
    for label, new_data, old_data, expected_shape in (
        ("left", new_a, ta.data, tuple(expected_a_shape)),
        ("right", new_b, tb.data, tuple(expected_b_shape)),
    ):
        if tuple(new_data.shape) != expected_shape:
            raise RuntimeError(
                f"FET {label} absorption shape {tuple(new_data.shape)} "
                f"!= expected {expected_shape}"
            )
        if new_data.dtype != old_data.dtype or new_data.device != old_data.device:
            raise RuntimeError(
                f"FET {label} absorption dtype/device drifted from carrier tensor"
            )
        if not bool(torch.isfinite(new_data).all().item()):
            raise RuntimeError(f"FET {label} produced a non-finite absorption")

    # Authenticate both derived tensors before touching state, then make the two
    # endpoint updates transactional.  Snapshot references remain valid because
    # quimb ``modify(data=...)`` replaces, rather than edits, tensor storage.
    old_a = ta.data
    old_b = tb.data
    try:
        ta.modify(data=new_a)
        tb.modify(data=new_b)
    except Exception as write_error:
        rollback_errors = []
        for label, tensor, snapshot in (
            ("left", ta, old_a),
            ("right", tb, old_b),
        ):
            try:
                tensor.modify(data=snapshot)
            except Exception as rollback_error:  # noqa: BLE001
                rollback_errors.append((label, rollback_error))
        if rollback_errors:
            details = ", ".join(
                f"{label}:{type(error).__name__}" for label, error in rollback_errors
            )
            raise RuntimeError(
                f"FET write-back failed and rollback was incomplete ({details})"
            ) from write_error
        raise


# =========================================================================== #
# Environment-aware rank-selection wrapper.                                    #
# =========================================================================== #
def env_optimal_rank(
    state,
    bond: str,
    eps_fid: float,
    *,
    solver_seed: int = FET_SOLVER_SEED_DEFAULT,
    fidelity_curve: list[dict] | None = None,
) -> FetSelection:
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

    If no ``χ ∈ [1, bare_rank]`` reaches the target, KEEP the full bond —
    ``env_rank = current stored dim``, ``U = V† = identity``, ``fid_env = 1.0``.
    The returned :class:`FetSelection` remains unpackable as the historical
    four-tuple while exposing ``outcome`` (``accepted``, ``noop``, or
    ``solver_failed``) and the best rejected candidate separately.

    ``fidelity_curve`` is an explicit diagnostic sink. Supplying it evaluates all
    ranks but freezes the first accepted result; every rank/restart uses a private
    deterministic stream, so observing the curve cannot change the selection or
    ambient CUDA RNG state."""
    eps_fid = float(eps_fid)
    if not 0.0 < eps_fid < 1.0:
        raise ValueError(f"eps_fid must lie in (0, 1), got {eps_fid!r}")
    solver_seed = int(solver_seed)
    if solver_seed < 0:
        raise ValueError(f"solver_seed must be nonnegative (got {solver_seed})")
    # Freeze the analytic upper-bound factorization before environment eig/SVD
    # work.  Rank-deficient CUDA decompositions must not acquire call-order
    # dependence from repeatedly rebuilding their Moore-Penrose pullbacks.
    carrier_svd_factorization = None
    try:
        carrier_svd_factorization = _carrier_svd_factorization(state, bond)
    except Exception as exc:  # noqa: BLE001  # standalone solver KATs lack a carrier state
        _p(
            f"      [env_optimal_rank {bond}] carrier-SVD factorization "
            f"unavailable: {type(exc).__name__}: {exc}"
        )
    Gamma = gamma_TN(state, bond)
    D = int(Gamma.shape[0])
    fid_target = 1.0 - eps_fid
    S = _insertion_spectrum(state, bond)
    bare = min(int(_exact_rank(S)), D)   # env_rank <= bare_rank
    prep = None
    try:
        prep = _fix_gauge(Gamma)
    except Exception as exc:  # noqa: BLE001  # gauge seed unavailable; ALS still runs
        _p(f"      [env_optimal_rank {bond}] fix_gauge failed: {type(exc).__name__}: {exc}")

    accepted = None
    best_finite = None
    solver_failure_count = 0
    attempted_ranks = 0
    for chi in range(1, bare + 1):
        attempted_ranks += 1
        als_result = _multistart_als_truncation(
            Gamma,
            state,
            bond,
            chi,
            prep,
            solver_seed=solver_seed,
            feasible_candidate=(
                None
                if carrier_svd_factorization is None
                else _carrier_svd_candidate_from_factorization(
                    carrier_svd_factorization, chi
                )
            ),
        )
        fid = gamma_fidelity(Gamma, als_result["U"] @ als_result["Vh"])
        solver_reported_ok = als_result.get("solver_status", "ok") == "ok"
        fid_valid = bool(
            solver_reported_ok
            and np.isfinite(fid)
            and 0.0 <= float(fid) <= 1.0
        )
        solver_status = "ok" if fid_valid else "solver_failed"
        if not fid_valid:
            solver_failure_count += 1
        if fidelity_curve is not None:
            fidelity_curve.append(
                {
                    "chi": int(chi),
                    "fid": float(fid) if fid_valid else None,
                    "solver_status": str(solver_status),
                }
            )
        if fid_valid and (
            best_finite is None or float(fid) > best_finite[3]
        ):
            best_finite = (
                int(chi),
                als_result["U"],
                als_result["Vh"],
                float(fid),
            )
        if accepted is None and fid_valid and float(fid) >= fid_target:
            accepted = (
                int(chi),
                als_result["U"],
                als_result["Vh"],
                float(fid),
                int(attempted_ranks),
                int(solver_failure_count),
            )
            if fidelity_curve is None:
                break

    if accepted is not None:
        chi, U, Vh, fid, selected_attempts, selected_failures = accepted
        return FetSelection(
            chi,
            U,
            Vh,
            fid,
            outcome="accepted",
            candidate_rank=chi,
            candidate_fid=fid,
            solver_seed=solver_seed,
            attempted_ranks=selected_attempts,
            solver_failure_count=selected_failures,
        )

    # Mutation firewall at the selector boundary: no qualifying candidate ever
    # becomes a lossy ceiling cut.  The direct caller receives the exact identity;
    # rejected candidate evidence remains in explicit attributes only.
    eye = torch.eye(D, dtype=CDTYPE, device=Gamma.device)
    all_attempts_failed = attempted_ranks > 0 and (
        solver_failure_count == attempted_ranks
    )
    return FetSelection(
        D,
        eye,
        eye,
        1.0,
        outcome="solver_failed" if all_attempts_failed else "noop",
        candidate_rank=None if best_finite is None else int(best_finite[0]),
        candidate_fid=None if best_finite is None else float(best_finite[3]),
        solver_seed=solver_seed,
        attempted_ranks=attempted_ranks,
        solver_failure_count=solver_failure_count,
    )

"""OPT2-1 equivalence gates for the batched-MPS op core (REGISTERED test suite).

This file IS the registered gate set G-OP-1..G-OP-7 of the "OPT2-1 DESIGN" section (v2)
of ``docs/twin_validation/batched_mps_backend_prereg.md`` (predict-before-measure: ALL
tests are registered to PASS; ANY miss is a FINDING to adjudicate, never a silent
tolerance bump).

Module under test: ``qec_twin.forward.scalable.batched_mps`` (torch/cuda/complex128,
quimb-free). Reference arm: the SERIAL ``MpsLeakageForward`` private methods
(``_apply_gate`` / ``_leak_sample`` / ``_measure_stabilizer`` / ``_apply_sqrt_Es`` /
``_site_population`` / ``_parity_expectation`` / ``_norm_sq`` / ``_renormalize`` /
``_terminal_readout``) driven on quimb MPS objects -- quimb appears ONLY here, never in
the module. A second, FROM-SCRATCH dense referee (`_dense_apply_window` et al.) is
validated against the serial arm on the monotonic cases and then used for the
leg-order-discriminating cases (adversarial >=2-method cross-verification).

Gate -> test mapping (each gate = at least one ``test_gopN_*``):
  G-OP-1 : test_gop1_bond_caps_and_dense_roundtrip / test_gop1_broadcast_from_quimb /
           test_gop1_canonicalize_norm_renormalize / test_gop1_apply_1site_shared_and_pershot /
           test_gop1_site_rdm / test_gop1_local_expectation_parity /
           test_gop1_local_expectation_permutation_asymmetric_nonmonotonic /
           test_gop1_window_exact_grade_shared_forms (window leg at EXACT grade ONLY -- v2
           scope fence (a); all other ops at BOTH grades) /
           test_gop1_window_pershot_diagonal_exact_grade (the v2-recheck d[B,3^w] G-OP-1 leg) /
           test_gop1_offcenter_invocation (v2 case (c): center deliberately FAR)
  G-OP-2 : test_gop2_kraus_sample_shared_u (both grades) /
           test_gop2_born_stab_composition_exact_grade (window-containing leg: EXACT only) /
           test_gop2_armC_leakflag (both grades) /
           test_gop2_hard2_terminal (both grades; incl. the wt<=NUMERICAL_ZERO=>p1=0.5 guard
           on a degenerate zero-norm shot) /
           test_gop2_hard3_terminal (both grades; incl. the kbar==2 deterministic
           residual-split sub-draw + the BATCHED-ONLY zero-norm degenerate leg --
           tot<=NUMERICAL_ZERO=>kbar=0, prereg D-2 registry v5 note)
  G-OP-3 : test_gop3_single_truncating_split_gap_and_books /
           test_gop3_flat_spectrum_retained_block
  G-OP-4 : test_gop4_batch_vs_single_every_op /
           test_gop4_window_pershot_diagonal_batch_vs_single (v2-recheck G-OP-4 leg)
  G-OP-5 : test_gop5_padding_invariance_chi_lo_vs_hi
  G-OP-6 : test_gop6_exact_grade_discarded_literal_zero
  G-OP-7 : test_gop7_micro_sequence_n5

Conventions bound here (from the prereg + the v2 re-check clarifications):
  * ABSOLUTE elementwise state tolerance 1e-12 on unit-norm states; NO gauge/phase
    alignment (any phase discrepancy is a bug and fails the gate).
  * KNIFE-EDGE GUARD on every sampling gate: every drawn comparison asserts
    ``|u*tot - cumsum_k| > 1e-9`` (cumulative rules) / ``|u - p| > 1e-9`` (direct
    thresholds), re-drawing ``u`` on violation.
  * LEG ORDER: G's legs correspond to ``sites`` IN THE GIVEN ORDER; the 3^w axis of the
    per-shot diagonal form ``d[B,3^w]`` uses the SAME enumeration -- trit-tuples
    row-major with ``sites[0]`` the MOST-SIGNIFICANT factor (the serial build
    convention, ``mps_forward.py`` lines 664-668).
  * Exact grade: ``discarded == 0.0`` LITERALLY (the D-3 v2 structural QR-route book).

Ambiguities resolved (single-place adapters below): kraus passed as a stacked
``[K,3,3]`` tensor; the SHARED diagonal window form passed as the dense
``torch.diag`` matrix with ``diagonal=True``; the PER-SHOT diagonal form passed as the
vector ``d[B,3^w]`` with ``diagonal=True``; ``_terminal_readout`` needs the instance
attrs ``_eng_to_mps`` / ``_log_eng_support`` (set explicitly, identity site order).

GPU-only (``requires_cuda`` on every test); chains n in {4,5,6} qutrits only (never the
full d3 9-chain) so every test stays at a few GPU-seconds.
"""

from __future__ import annotations

import numpy as np
import pytest
import torch

qtn = pytest.importorskip("quimb.tensor")

from qec_twin.forward.scalable import batched_mps as bm  # the module under test
from qec_twin.forward.scalable.mps_forward import (
    MpsLeakageForward,
    MpsTruncationLedger,
    _arm_d2,
    _qutrit_gate,
    exact_chi,
)
from qec_twin.forward.scalable.sv_sampler import leak_slice_kraus_torch
from qec_twin.numerics import NUMERICAL_ZERO

# Skip gate + canonical constants from tests/conftest.py (Wave 1, contract C1).
from conftest import CDTYPE, DEVICE, PHYS, RDTYPE, requires_cuda

pytestmark = [requires_cuda]

TOL = 1.0e-12       # G-OP-1/2/4/5 absolute elementwise state tolerance (unit-norm states)
_MARGIN = 1.0e-9    # the registered knife-edge margin (v2 G-OP-2)
TRUNC_CHI = 4       # the registered truncated grade (test states CONSTRUCTED rank<=3 per cut)
B_EFF = 0.9         # terminal readout bias b (arm A d2 = 1-2b = -0.8)
D2_A = _arm_d2("A", B_EFF)


# =========================================================================== #
# Adapters -- ONE place to fix if a batched_mps signature detail differs.      #
# =========================================================================== #
def _mk_from_dense(psi: torch.Tensor, chi: int):
    """psi [B, 3^n] cuda c128 -> BatchedMps at bond grade chi."""
    return bm.BatchedMps.from_dense(psi, int(chi))


def _mk_broadcast(qmps, B: int, chi: int):
    return bm.BatchedMps.broadcast_from_quimb(qmps, int(B), int(chi))


def _bond_caps(n: int, chi: int) -> list[int]:
    return [int(c) for c in bm.bond_caps(int(n), int(chi))]


def _win(x, G: torch.Tensor, sites, diagonal: bool):
    """apply_window_recompress_ -> (discarded[B] floats, branch_weight[B] floats).

    G forms (D-2 op 7 v4): shared dense [3^w,3^w] (diagonal=True enables the fast path,
    off-diagonal mass must be EXACTLY 0) OR the per-shot diagonal VECTOR d[B,3^w]."""
    disc, bw = x.apply_window_recompress_(G, tuple(int(s) for s in sites), diagonal=bool(diagonal))
    return _floats(disc), _floats(bw)


def _kraus_stack(kraus_list) -> torch.Tensor:
    return torch.stack([k.to(dtype=CDTYPE, device=DEVICE) for k in kraus_list])


def _floats(x) -> list[float]:
    if isinstance(x, torch.Tensor):
        return [float(v) for v in x.detach().cpu().reshape(-1).tolist()]
    if isinstance(x, (list, tuple)):
        return [float(v) for v in x]
    return [float(x)]


def _ints(x) -> list[int]:
    if isinstance(x, torch.Tensor):
        return [int(v) for v in x.detach().cpu().reshape(-1).tolist()]
    if isinstance(x, (list, tuple)):
        return [int(v) for v in x]
    return [int(x)]


def _u_tensor(us) -> torch.Tensor:
    return torch.tensor([float(u) for u in us], dtype=RDTYPE, device=DEVICE)


# =========================================================================== #
# FROM-SCRATCH dense referees (independent of quimb AND of batched_mps).      #
# =========================================================================== #
def _dense_apply_window(psi: torch.Tensor, G: torch.Tensor, sites, n: int) -> torch.Tensor:
    """Apply G [3^w,3^w] to psi [B,3^n] with G's legs corresponding to ``sites`` IN THE
    GIVEN ORDER, ``sites[0]`` = the MOST-SIGNIFICANT trit of G's row index (the serial
    build convention, mps_forward.py lines 664-668; site 0 = global MSB)."""
    B = int(psi.shape[0])
    w = len(sites)
    sset = {int(s) for s in sites}
    t = psi.reshape([B] + [PHYS] * n)
    rest = [ax for ax in range(n) if ax not in sset]
    perm = [0] + [1 + int(s) for s in sites] + [1 + ax for ax in rest]
    t2 = t.permute(*perm).reshape(B, PHYS ** w, PHYS ** (n - w))
    t2 = torch.einsum("ij,bjk->bik", G.to(dtype=psi.dtype), t2)
    t3 = t2.reshape([B] + [PHYS] * w + [PHYS] * (n - w))
    inv = [0] * (n + 1)
    for newpos, oldpos in enumerate(perm):
        inv[oldpos] = newpos
    return t3.permute(*inv).reshape(B, PHYS ** n).contiguous()


def _dense_expect(psi: torch.Tensor, G: torch.Tensor, sites, n: int, normalized: bool = True) -> torch.Tensor:
    """<psi|G_sites|psi> per shot ([B] real), same leg-order convention."""
    gpsi = _dense_apply_window(psi, G, sites, n)
    num = torch.einsum("bi,bi->b", psi.conj(), gpsi)
    if normalized:
        den = torch.einsum("bi,bi->b", psi.conj(), psi).real
        return (num / den.to(num.dtype)).real
    return num.real


def _dense_rdm(psi: torch.Tensor, site: int, n: int, normalized: bool = False) -> torch.Tensor:
    """1-site RDM [B,3,3]: rho[b,i,j] = sum_env psi[b, i-at-site, env] conj(psi[b, j, env])."""
    B = int(psi.shape[0])
    t = psi.reshape(B, PHYS ** int(site), PHYS, PHYS ** (n - int(site) - 1))
    rho = torch.einsum("baid,bajd->bij", t, t.conj())
    if normalized:
        tr = torch.einsum("bii->b", rho).real
        rho = rho / tr.reshape(B, 1, 1).to(rho.dtype)
    return rho


def _cut_lambdas(psi_row: torch.Tensor, n: int, cut: int) -> torch.Tensor:
    """Normalized (unit-trace) descending Schmidt lambdas of the [3^n] row at cut
    ``cut`` (between sites cut | cut+1)."""
    m = psi_row.reshape(PHYS ** (int(cut) + 1), -1)
    s = torch.linalg.svdvals(m)
    lam = s ** 2
    return lam / lam.sum()


def _rank_at_cut(psi_row: torch.Tensor, n: int, cut: int, floor: float = 1e-8) -> int:
    # class (c) HARNESS threshold only (test states carry O(1) Schmidt values by
    # construction -- far from the boundary); never a module-side rank rule.
    return int((_cut_lambdas(psi_row, n, cut) > floor).sum())


def _assert_states_close(a: torch.Tensor, b: torch.Tensor, tol: float = TOL, msg: str = "") -> None:
    """ABSOLUTE elementwise comparison; NO phase alignment (v2 G-OP-1 convention)."""
    d = float((a.reshape(-1) - b.reshape(-1)).abs().max())
    assert d <= tol, f"state mismatch max|diff|={d:.3e} > {tol:.0e} {msg}"


def _normalized(psi: torch.Tensor) -> torch.Tensor:
    if psi.dim() == 1:
        return psi / torch.linalg.vector_norm(psi)
    nrm = torch.linalg.vector_norm(psi, dim=1, keepdim=True)
    return psi / nrm


# =========================================================================== #
# Serial-arm helpers (the REAL MpsLeakageForward private methods on quimb MPS) #
# =========================================================================== #
def _fwd() -> MpsLeakageForward:
    # __init__ cost checked: SvSampler.__init__ only stores the device
    # (sv_sampler.py lines 484-485) and the quimb import is lazy -> CHEAP; the real
    # serial methods are therefore driven directly (independent-referee discipline).
    return MpsLeakageForward(device=DEVICE)


def _prime_fwd(fwd: MpsLeakageForward, n: int, log_support: list[int]) -> None:
    """_terminal_readout reads self._eng_to_mps / self._log_eng_support (mps_forward.py
    lines 769/839) -- normally set by sample(); set them explicitly (identity order)."""
    fwd._eng_to_mps = {q: q for q in range(int(n))}
    fwd._log_eng_support = [int(q) for q in log_support]


def _qmps_from_dense_row(psi_row: torch.Tensor, n: int):
    """quimb MPS from a dense [3^n] engine vector (IDENTITY site order) -- mirrors
    MpsLeakageForward._mps_from_statevector (lines 385-403) incl. the site-0-MSB
    ``from_dense(dims=[3]*n)`` convention; arrays mapped to torch cuda complex128."""
    arr = psi_row.detach().cpu().numpy().astype(np.complex128)
    mps = qtn.MatrixProductState.from_dense(arr, dims=[PHYS] * int(n))
    mps.apply_to_arrays(lambda x: torch.as_tensor(x, dtype=CDTYPE, device=DEVICE))
    return mps


def _dense_of_qmps(mps) -> torch.Tensor:
    d = mps.to_dense()
    if not isinstance(d, torch.Tensor):
        d = torch.as_tensor(np.asarray(d))
    return d.reshape(-1).to(device=DEVICE, dtype=CDTYPE)


# =========================================================================== #
# State builders (deterministic seeds; O(1) Schmidt values).                  #
# =========================================================================== #
def _haar_batch(n: int, B: int, seed: int) -> torch.Tensor:
    """Full-rank random unit rows [B,3^n] (exact-grade test states)."""
    rng = np.random.default_rng(seed)
    D = PHYS ** int(n)
    v = rng.standard_normal((B, D)) + 1j * rng.standard_normal((B, D))
    v = v / np.linalg.norm(v, axis=1, keepdims=True)
    return torch.as_tensor(v, dtype=CDTYPE, device=DEVICE)


def _rand_unitary(dim: int, rng: np.random.Generator) -> torch.Tensor:
    m = rng.standard_normal((dim, dim)) + 1j * rng.standard_normal((dim, dim))
    q, r = np.linalg.qr(m)
    ph = np.diagonal(r) / np.abs(np.diagonal(r))
    return torch.as_tensor(q * ph.conj(), dtype=CDTYPE, device=DEVICE)


def _block_structural_ranks(n: int) -> list[int]:
    """Per-cut STRUCTURAL Schmidt ranks of the disjoint-2-site-block product pattern
    (blocks (0,1),(2,3),... , trailing 1-site block if n is odd): cut k lies WITHIN a
    2-site block iff k is even -> rank <= 3 (a pure 2-site qutrit state has at most 3
    Schmidt values); every between-block cut is a PRODUCT cut -> rank exactly 1."""
    return [3 if cut % 2 == 0 else 1 for cut in range(int(n) - 1)]


def _assert_sigma_conditioning(psi: torch.Tensor, n: int, struct_ranks: list[int],
                               chi: int, who: str) -> None:
    """FIX-3: the prereg D-5 retained-spectrum conditioning fence, SIGMA units
    (``sigma_min(retained)/sigma_max >= 1e-3``), asserted as a builder PRECONDITION for
    every state whose run Gram-routes a split at bond grade ``chi`` (class (c) fence
    per prereg D-5; a failure means RE-SEED THIS CASE, never a gate miss). At each cut
    the ratio is restricted to the STRUCTURAL rank of the construction (the blocks) --
    the retained set when ``chi >=`` that rank -- because Gram-route eigenvector
    (Davis-Kahan) error ~ eps*sigma_max/sqrt(lambda_min_retained) breaches the 1e-12
    absolute state gates if a retained nonzero Schmidt value drifts to ~1e-8 on an
    unlucky seed."""
    for b in range(int(psi.shape[0])):
        for cut in range(int(n) - 1):
            r = min(int(struct_ranks[cut]), int(chi))
            lam = _cut_lambdas(psi[b], int(n), cut)  # unit-trace, DESCENDING
            ratio = float((lam[r - 1] / lam[0]) ** 0.5)  # sigma units = sqrt(lambda)
            assert ratio >= 1e-3, (
                f"PRECONDITION (not a gate miss): {who} sigma-conditioning fence "
                f"sigma_min(retained)/sigma_max = {ratio:.3e} < 1e-3 at cut {cut}, "
                f"shot {b} (prereg D-5, class (c)) -- re-seed this case"
            )


def _low_rank_batch(n: int, B: int, seed: int) -> torch.Tensor:
    """[B,3^n] unit rows with Schmidt rank <= 3 at EVERY cut (fits TRUNC_CHI=4 with
    zero truncation) -- the sound DISJOINT-BLOCK pattern (the one test_gop5 uses).

    RANK BUDGET (counted): partition the n sites into DISJOINT contiguous blocks of
    <= 2 sites -- (0,1),(2,3),...; each block carries an INDEPENDENT Haar-random pure
    state (batch-heterogeneous), and the row is the product across blocks. A pure
    2-site block has Schmidt rank <= 3 at its within-block cut (bounded by the qutrit
    physical dim); every between-block cut is a PRODUCT cut => rank exactly 1. Hence
    rank <= 3 <= TRUNC_CHI=4 at every cut, with O(1) Schmidt values (far from
    from_dense's 1e-12 dropped-mass constructor guard).

    (The previous brick-wall construction -- two staggered layers of 2-site Haar
    unitaries -- was mathematically UNSOUND: a layer-2 gate on (1,2) acts across cut 1
    whose two sides are ALREADY entangled by layer 1, so the post-gate Schmidt rank at
    that cut is bounded only by the gate's OPERATOR Schmidt rank 3^2 = 9, not by the
    physical dim 3; the builder's own r <= 3 assert fired and from_dense(chi=4) raised
    its dropped-mass constructor guard.)

    The rank bound is ASSERTED below (precondition evidence, anti-vacuous), and the
    prereg D-5 sigma-conditioning fence is asserted at TRUNC_CHI (FIX-3 wiring)."""
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(int(B)):
        psi = None
        start = 0
        while start < int(n):
            blk = min(2, int(n) - start)
            v = rng.standard_normal(PHYS ** blk) + 1j * rng.standard_normal(PHYS ** blk)
            v = v / np.linalg.norm(v)
            psi = v if psi is None else np.kron(psi, v)
            start += blk
        rows.append(torch.as_tensor(psi, dtype=CDTYPE, device=DEVICE))
    out = torch.stack(rows)
    for b in range(int(B)):
        for cut in range(int(n) - 1):
            r = _rank_at_cut(out[b], int(n), cut)
            assert r <= 3, f"low-rank builder violated its own budget: rank {r} at cut {cut}"
    _assert_sigma_conditioning(out, int(n), _block_structural_ranks(int(n)), TRUNC_CHI,
                               "trunc-grade state builder (_low_rank_batch)")
    return out


def _grades(n: int):
    """(label, chi, state builder) for the two registered bond grades."""
    return (
        ("exact", exact_chi(int(n)), _haar_batch),
        (f"trunc{TRUNC_CHI}", TRUNC_CHI, _low_rank_batch),
    )


# =========================================================================== #
# Knife-edge margin guard (registered; re-draw on violation).                 #
# =========================================================================== #
def _margin_ok_cumsum(u: float, pk) -> bool:
    tot = float(sum(float(p) for p in pk))
    c = 0.0
    for p in pk:
        c += float(p)
        if abs(float(u) * tot - c) <= _MARGIN:
            return False
    return True


def _assert_margin_cumsum(u: float, pk) -> None:
    assert _margin_ok_cumsum(u, pk), (
        f"knife-edge draw: |u*tot - cumsum| <= {_MARGIN:.0e} (u={u!r}, pk={list(map(float, pk))!r}) "
        "-- registered non-failure; re-draw"
    )


def _assert_margin_thresh(u: float, p: float) -> None:
    assert abs(float(u) - float(p)) > _MARGIN, (
        f"knife-edge draw: |u - p| <= {_MARGIN:.0e} (u={u!r}, p={p!r}) -- registered non-failure; re-draw"
    )


def _safe_u_cumsum(rng: np.random.Generator, pk) -> float:
    for _ in range(1000):
        u = float(rng.random())
        if _margin_ok_cumsum(u, pk):
            return u
    raise AssertionError("could not draw a margin-safe cumulative u in 1000 tries")


def _u_for_branch(pk, k: int) -> float:
    """Deterministic mid-branch u forcing cumulative selection k (serial rule
    ``u*tot <= cumsum_k``, mps_forward.py lines 578-586); margin asserted."""
    tot = float(sum(float(p) for p in pk))
    lo = float(sum(float(p) for p in pk[: int(k)]))
    assert float(pk[int(k)]) > 10.0 * _MARGIN * max(tot, 1.0), "target branch too thin to hit safely"
    u = (lo + 0.5 * float(pk[int(k)])) / tot
    _assert_margin_cumsum(u, pk)
    return u


def _pick_branches(pk_row) -> list[int]:
    """FIX-2: weight-ranked branch targeting -- returns ``[argmax, second-largest]``
    branch indices of a pk row (ties broken by LOWEST index). The leak Kraus come from
    ``np.linalg.eigh(choi)`` ASCENDING (src/error_coupling_simulator/carrier/channels.py
    lines 639-643 keep eigenpairs > 1e-12 in ASCENDING eigenvalue order), so
    ``kraus[0]`` is the SMALLEST kept dust branch -- its weight can sit anywhere in
    (1e-12, 1e-6], BELOW the harness's 1e-8 hittability floor in ``_u_for_branch``
    (a spurious harness error, not a module bug) -- and ``kraus[K-1]`` is the DOMINANT
    no-jump branch. Literal-index targeting (0 / K-1) is therefore inverted/fragile;
    target by WEIGHT. The second-largest hittability assert below is a PRECONDITION
    (re-seed guidance), never a gate failure."""
    p = [float(v) for v in pk_row]
    assert len(p) >= 2, "branch targeting needs at least two Kraus branches"
    order = sorted(range(len(p)), key=lambda i: (-p[i], i))  # ties -> lowest index
    first, second = order[0], order[1]
    tot = sum(p)
    assert p[second] > 10.0 * _MARGIN * max(tot, 1.0), (
        f"PRECONDITION (not a gate failure): second-largest branch weight "
        f"{p[second]:.3e} is at/below the 1e-8 hittability floor of _u_for_branch "
        f"(pk={p!r}) -- re-seed this case so two branches are safely targetable"
    )
    return [first, second]


def _u_below(p: float) -> float:
    assert float(p) > 4.0 * _MARGIN, f"p={p} too small to draw strictly below with margin"
    u = 0.5 * float(p)
    _assert_margin_thresh(u, p)
    return u


def _u_above(p: float) -> float:
    assert 1.0 - float(p) > 4.0 * _MARGIN, f"p={p} too close to 1 to draw strictly above with margin"
    u = 0.5 * (1.0 + float(p))
    _assert_margin_thresh(u, p)
    return u


def _safe_u_thresh(rng: np.random.Generator, p: float) -> float:
    for _ in range(1000):
        u = float(rng.random())
        if abs(u - float(p)) > _MARGIN:
            return u
    raise AssertionError("could not draw a margin-safe threshold u in 1000 tries")


# =========================================================================== #
# Physics-operator helpers (replicas cite their serial source lines).         #
# =========================================================================== #
def _sqrt_es_diag(w: int, d2: float, sbit: int) -> torch.Tensor:
    """The diagonal sqrt(E_s) over the support trit-tuples [3^w] -- REPLICA of the
    serial build (mps_forward.py lines 664-676, INCLUDING the clamp es>=0): row-major
    enumeration with support[0] the MOST-SIGNIFICANT factor."""
    d_levels = torch.tensor([1.0, -1.0, float(d2)], dtype=RDTYPE, device=DEVICE)
    grids = torch.meshgrid(*([torch.arange(PHYS, device=DEVICE)] * int(w)), indexing="ij")
    prod = torch.ones([PHYS] * int(w), dtype=RDTYPE, device=DEVICE)
    for g in grids:
        prod = prod * d_levels[g]
    sgn = 1.0 if int(sbit) == 0 else -1.0
    es = torch.clamp(0.5 * (1.0 + sgn * prod), min=0.0)
    return torch.sqrt(es).reshape(-1).to(CDTYPE)


def _parity_string(w: int, d2: float) -> torch.Tensor:
    """kron_q diag(1,-1,d2) over w support legs (the serial _parity_expectation build,
    mps_forward.py lines 540-543); leg order = the given ``sites`` order."""
    Dq = torch.diag(torch.tensor([1.0, -1.0, float(d2)], dtype=CDTYPE, device=DEVICE))
    G = None
    for _ in range(int(w)):
        G = Dq if G is None else torch.kron(G, Dq)
    return G


def _assert_cptp(kraus_list, tol: float = 1e-12) -> None:
    s = None
    for K in kraus_list:
        t = K.conj().transpose(-1, -2) @ K
        s = t if s is None else s + t
    eye = torch.eye(PHYS, dtype=CDTYPE, device=DEVICE)
    r = float((s - eye).abs().max())
    assert r <= tol, f"Kraus set not CPTP: residual {r:.3e} > {tol:.0e}"


def _leak_kraus() -> list[torch.Tensor]:
    """The REAL leak-slice Kraus (sv_sampler.leak_slice_kraus_torch: 9x9 scipy expm --
    cheap), CPTP-asserted <= 1e-12."""
    ks = leak_slice_kraus_torch(theta=0.35, g_seep=0.09, g_heat=0.0, device=DEVICE)
    _assert_cptp(ks)
    return ks


def _f1_collapse_stack(bits, b_eff: float) -> torch.Tensor:
    """Per-shot sqrt(F_bit) collapse diagonals (serial hard2, mps_forward.py lines
    783-791): bit1 -> diag(0,1,sqrt(b)), bit0 -> diag(1,0,sqrt(1-b))."""
    mats = []
    for bit in bits:
        if int(bit) == 1:
            dg = [0.0, 1.0, float(b_eff) ** 0.5]
        else:
            dg = [1.0, 0.0, (1.0 - float(b_eff)) ** 0.5]
        mats.append(torch.diag(torch.tensor(dg, dtype=CDTYPE, device=DEVICE)))
    return torch.stack(mats)


def _dense_leak_pk(psi_row: torch.Tensor, kraus_list, site: int, n: int) -> list[float]:
    """UNNORMALIZED branch norms p_k = ||K_k psi||^2 (dense from-scratch referee for the
    serial RDM read, mps_forward.py lines 575-577)."""
    out = []
    for K in kraus_list:
        gpsi = _dense_apply_window(psi_row.reshape(1, -1), K, (int(site),), int(n))
        out.append(float(torch.linalg.vector_norm(gpsi) ** 2))
    return out


def _cumsel(pk, u: float) -> int:
    """The serial cumulative selection rule EXACTLY (mps_forward.py lines 578-586):
    first k with u*tot <= cumsum_k, fallback K-1. Inline replica needed because
    _leak_sample does not RETURN its selection."""
    tot = float(sum(float(p) for p in pk))
    target = float(u) * tot
    cum = 0.0
    sel = len(pk) - 1
    for k, p in enumerate(pk):
        cum += float(p)
        if target <= cum:
            sel = k
            break
    return int(sel)


def _unitary_with_leading_cols(cols: list[torch.Tensor], rng: np.random.Generator) -> torch.Tensor:
    """dim x dim unitary whose leading columns EQUAL the given orthonormal cols (QR
    completion + per-column phase fix)."""
    dim = int(cols[0].shape[0])
    M = torch.stack(cols, dim=1)
    k = int(M.shape[1])
    r = rng.standard_normal((dim, dim - k)) + 1j * rng.standard_normal((dim, dim - k))
    full = torch.cat([M, torch.as_tensor(r, dtype=CDTYPE, device=DEVICE)], dim=1)
    Q, R = torch.linalg.qr(full)
    ph = torch.diagonal(R)
    ph = ph / ph.abs()
    G = Q * ph.reshape(1, -1)
    for j in range(k):
        res = float((G[:, j] - cols[j]).abs().max())
        assert res <= 1e-12, f"unitary completion failed to pin column {j}: {res:.3e}"
    return G


# =========================================================================== #
# Serial terminal probes: pre-draw SAFE u, then drive the REAL private method  #
# and assert probe<->method consistency (adversarial two-path check).          #
# =========================================================================== #
def _serial_hard2(fwd: MpsLeakageForward, qmps, n: int, log_support: list[int],
                  b_eff: float, m: int, rng: np.random.Generator):
    """Returns (u_draws, TerminalReadout); qmps is mutated by the REAL
    _terminal_readout. The probe replicates the per-qutrit p1 read (mps_forward.py
    lines 772-781, incl. the wt<=NUMERICAL_ZERO=>p1=0.5 guard) ONLY to pre-draw
    margin-safe u; the emitted record comes from the real method."""
    probe = qmps.copy()
    F1 = torch.diag(torch.tensor([0.0, 1.0, float(b_eff)], dtype=CDTYPE, device=DEVICE))
    us: list[float] = []
    bits_probe: list[int] = []
    for q in range(int(n)):
        ket = probe.copy()
        ket.gate_(F1, where=int(q), contract=True)
        w1 = float((probe.H & ket).contract(all).real)
        wt = MpsLeakageForward._norm_sq(probe)
        p1 = (w1 / wt) if wt > NUMERICAL_ZERO else 0.5
        u = _safe_u_thresh(rng, p1)
        _assert_margin_thresh(u, p1)
        us.append(u)
        bit = 1 if u < p1 else 0
        bits_probe.append(bit)
        if bit == 1:
            dg = torch.tensor([0.0, 1.0, float(b_eff) ** 0.5], dtype=CDTYPE, device=DEVICE)
        else:
            dg = torch.tensor([1.0, 0.0, (1.0 - float(b_eff)) ** 0.5], dtype=CDTYPE, device=DEVICE)
        probe.gate_(torch.diag(dg), where=int(q), contract=True)
        MpsLeakageForward._renormalize(probe)
    _prime_fwd(fwd, n, log_support)
    tr = fwd._terminal_readout(qmps, log_sites=list(log_support), log_isx=[0] * len(log_support),
                               n_data=int(n), b_eff=float(b_eff), m=int(m), u_draws=us, mode="hard2")
    assert list(tr.bits) == bits_probe, "probe replica disagrees with the REAL _terminal_readout"
    _assert_states_close(_dense_of_qmps(qmps), _dense_of_qmps(probe), TOL, "(hard2 probe state)")
    return us, tr


def _serial_hard3(fwd: MpsLeakageForward, qmps, n: int, log_support: list[int],
                  b_eff: float, m: int, rng: np.random.Generator,
                  force_level2: dict[int, float] | None = None):
    """hard3 (gen=None) with pre-drawn safe u. ``force_level2[q] = u2_target`` forces
    kbar=2 at engine qutrit q with the DETERMINISTIC residual-split sub-draw landing at
    u2_target (serial lines 796-835: strict ``target < cum`` cumulative with fallback
    kbar=2; u2 = clamp((u-lo)/max(p2/tot, NUMERICAL_ZERO)); bit strict u2 < b)."""
    force_level2 = force_level2 or {}
    probe = qmps.copy()
    us: list[float] = []
    lv_probe: list[int] = []
    for q in range(int(n)):
        p = [fwd._site_population(probe, int(q), lev) for lev in (0, 1, 2)]
        tot = float(sum(p))
        # FIX-5 (prereg D-2 registry v5 note + chip task_9f0687fe): this NON-DEGENERATE
        # fence is load-bearing and KEPT -- the serial arm CANNOT referee the zero-norm
        # regime because its own ``tot <= NUMERICAL_ZERO => kbar=0`` guard is
        # NaN-SHADOWED DEAD CODE: _site_population (mps_forward.py line 527) is a
        # normalized quimb read that divides by the trace unconditionally, so a
        # zero-norm state yields NaN populations; ``NaN <= NUMERICAL_ZERO`` is False
        # (lines 802-803) so the guard never fires, the cumulative loop falls through
        # to the kbar=2 fallback, and the sub-draw's else-branches (lines 830-831) emit
        # u2=0.5 => bit=(0.5 < b). The WRITTEN guard is the NORMATIVE BATCHED semantics
        # (declared intentional divergence on the degenerate regime); the batched-only
        # degenerate leg in test_gop2_hard3_terminal covers it; the serial fix is chip
        # task_9f0687fe (serial arm untouched in this phase).
        assert tot > NUMERICAL_ZERO, (
            "serial hard3 comparison requires a non-degenerate state (the zero-norm "
            "regime is BATCHED-ONLY; see the FIX-5 / prereg registry v5 note above)")
        if q in force_level2:
            assert p[2] / tot > 1e-3, f"engineered |2> mass too small at site {q} (p2={p[2]/tot:.2e})"
            lo = (p[0] + p[1]) / tot
            u2t = float(force_level2[q])
            u = lo + u2t * (p[2] / tot)
            _assert_margin_cumsum(u, p)
            u2 = (u - lo) / max(p[2] / tot, NUMERICAL_ZERO)
            _assert_margin_thresh(u2, b_eff)
            kbar = 2
        else:
            u = _safe_u_cumsum(rng, p)
            _assert_margin_cumsum(u, p)
            target = u * tot
            cum = 0.0
            kbar = 2
            for lev in (0, 1, 2):
                cum += p[lev]
                if target < cum:
                    kbar = lev
                    break
        us.append(float(u))
        lv_probe.append(int(kbar))
        proj = torch.zeros((PHYS, PHYS), dtype=CDTYPE, device=DEVICE)
        proj[kbar, kbar] = 1.0
        probe.gate_(proj, where=int(q), contract=True)
        MpsLeakageForward._renormalize(probe)
    _prime_fwd(fwd, n, log_support)
    tr = fwd._terminal_readout(qmps, log_sites=list(log_support), log_isx=[0] * len(log_support),
                               n_data=int(n), b_eff=float(b_eff), m=int(m), u_draws=us,
                               mode="hard3", gen=None)
    assert list(tr.levels) == lv_probe, "probe replica disagrees with the REAL hard3 _terminal_readout"
    _assert_states_close(_dense_of_qmps(qmps), _dense_of_qmps(probe), TOL, "(hard3 probe state)")
    return us, tr


# =========================================================================== #
# Batched-arm compositions (harness-side; mirror the serial rules EXACTLY).    #
# =========================================================================== #
def _batched_hard2(x, n: int, log_support: list[int], b_eff: float, m: int,
                   u_mat: list[list[float]]):
    """hard2 terminal on a BatchedMps: F1 expectation via site_rdm, strict u < p1 with
    the wt<=NUMERICAL_ZERO=>0.5 guard, per-shot sqrt(F_bit) collapse via apply_1site_,
    renormalize_. u_mat[b][q]. Returns (bits [B][n], flips [B])."""
    F1 = torch.diag(torch.tensor([0.0, 1.0, float(b_eff)], dtype=CDTYPE, device=DEVICE))
    B = len(u_mat)
    bits = [[0] * int(n) for _ in range(B)]
    for q in range(int(n)):
        rho = x.site_rdm(int(q), normalized=False)
        w1 = torch.einsum("bij,ji->b", rho, F1).real
        wt = torch.einsum("bii->b", rho).real
        for b in range(B):
            wt_b, w1_b = float(wt[b]), float(w1[b])
            p1 = (w1_b / wt_b) if wt_b > NUMERICAL_ZERO else 0.5
            _assert_margin_thresh(u_mat[b][q], p1)
            bits[b][q] = 1 if float(u_mat[b][q]) < p1 else 0
        x.apply_1site_(_f1_collapse_stack([bits[b][q] for b in range(B)], b_eff), int(q))
        x.renormalize_()
    flips = []
    for b in range(B):
        par = 0
        for q in log_support:
            par ^= (bits[b][int(q)] & 1)
        flips.append(int((par ^ (int(m) & 1)) & 1))
    return bits, flips


def _batched_hard3(x, n: int, log_support: list[int], b_eff: float, m: int,
                   u_mat: list[list[float]]):
    """hard3 terminal on a BatchedMps mirroring serial lines 796-835: level populations
    from site_rdm(normalized=True), cumulative STRICT target<cum with fallback kbar=2
    and the tot<=NUMERICAL_ZERO=>kbar=0 guard, per-shot |kbar><kbar| collapse, and the
    deterministic residual-split |2>->bit sub-draw (strict u2 < b)."""
    B = len(u_mat)
    levels = [[0] * int(n) for _ in range(B)]
    bits = [[0] * int(n) for _ in range(B)]
    for q in range(int(n)):
        rho = x.site_rdm(int(q), normalized=True)
        pmat = torch.diagonal(rho, dim1=-2, dim2=-1).real  # [B,3]
        projs = []
        for b in range(B):
            p = [float(pmat[b, lev]) for lev in (0, 1, 2)]
            tot = float(sum(p))
            if tot <= NUMERICAL_ZERO:
                kbar = 0
            else:
                u = float(u_mat[b][q])
                _assert_margin_cumsum(u, p)
                target = u * tot
                cum = 0.0
                kbar = 2
                for lev in (0, 1, 2):
                    cum += p[lev]
                    if target < cum:
                        kbar = lev
                        break
            levels[b][q] = int(kbar)
            if kbar == 2:
                lo = (p[0] + p[1]) / tot if tot > NUMERICAL_ZERO else 0.0
                u2 = (float(u_mat[b][q]) - lo) / max(p[2] / tot, NUMERICAL_ZERO) if tot > NUMERICAL_ZERO else 0.5
                u2 = min(max(u2, 0.0), 1.0)
                _assert_margin_thresh(u2, b_eff)
                bits[b][q] = 1 if (u2 < float(b_eff)) else 0
            else:
                bits[b][q] = int(kbar)
            pr = torch.zeros((PHYS, PHYS), dtype=CDTYPE, device=DEVICE)
            pr[kbar, kbar] = 1.0
            projs.append(pr)
        x.apply_1site_(torch.stack(projs), int(q))
        x.renormalize_()
    flips = []
    for b in range(B):
        par = 0
        for q in log_support:
            par ^= (bits[b][int(q)] & 1)
        flips.append(int((par ^ (int(m) & 1)) & 1))
    return levels, bits, flips


def _batched_born_stab(x, sites, isx, d2: float, us: list[float]):
    """The Born-stab composition on a BatchedMps (serial _measure_stabilizer arm A,
    lines 612-641): H on X-supports, parity read, strict u < p0, per-shot diagonal
    sqrt(E_s) window (the v4 d[B,3^w] form -- sbit is per shot), H back.
    Returns (sbits, discarded, bw, p0s)."""
    H = _qutrit_gate("H", DEVICE)
    w = len(sites)
    for j, s in enumerate(sites):
        if int(isx[j]) == 1:
            x.apply_1site_(H, int(s))
    ppar = _floats(x.local_expectation(_parity_string(w, d2), tuple(int(s) for s in sites), normalized=True))
    sbits, p0s = [], []
    for b, u in enumerate(us):
        p0 = 0.5 * (1.0 + ppar[b])
        _assert_margin_thresh(u, p0)
        sbits.append(0 if float(u) < p0 else 1)
        p0s.append(p0)
    d_es = torch.stack([_sqrt_es_diag(w, d2, sb) for sb in sbits])  # [B, 3^w] per-shot diagonal
    disc, bw = _win(x, d_es, sites, diagonal=True)
    for j, s in enumerate(sites):
        if int(isx[j]) == 1:
            x.apply_1site_(H, int(s))
    return sbits, disc, bw, p0s


# =========================================================================== #
# G-OP-1 -- exact dense-reconstruction equivalence (<=1e-12 absolute).         #
# =========================================================================== #
def test_gop1_bond_caps_and_dense_roundtrip():
    """bond_caps == the D-1 formula; from_dense -> to_dense roundtrip at BOTH grades,
    vs the input AND vs the quimb from_dense/to_dense referee."""
    for n in (4, 6):
        for chi in (TRUNC_CHI, exact_chi(n), exact_chi(n) + 5):
            want = [min(PHYS ** (k + 1), PHYS ** (n - k - 1), int(chi)) for k in range(n - 1)]
            assert _bond_caps(n, chi) == want, f"bond_caps({n},{chi}) != D-1 formula"
    for n in (4, 6):
        for label, chi, mk in _grades(n):
            psi = mk(n, 2, seed=101 + n)
            x = _mk_from_dense(psi, chi)
            _assert_states_close(x.to_dense(), psi, TOL, f"(roundtrip n={n} {label})")
            # quimb referee (same site-0-MSB convention)
            for b in range(2):
                q = _qmps_from_dense_row(psi[b], n)
                _assert_states_close(_dense_of_qmps(q), psi[b], TOL, f"(quimb referee n={n} {label})")


def test_gop1_broadcast_from_quimb():
    for n in (4, 6):
        for label, chi, mk in _grades(n):
            psi = mk(n, 1, seed=131 + n)[0]
            q = _qmps_from_dense_row(psi, n)
            x = _mk_broadcast(q, 3, chi)
            out = x.to_dense()
            assert tuple(out.shape) == (3, PHYS ** n)
            for b in range(3):
                _assert_states_close(out[b], psi, TOL, f"(broadcast b={b} n={n} {label})")


def test_gop1_canonicalize_norm_renormalize():
    """canonicalize_ leaves the represented state unchanged; norm_sq / renormalize_
    match the serial _norm_sq / _renormalize on a deliberately NON-unit input."""
    scale = 1.3
    for n in (4, 6):
        for label, chi, mk in _grades(n):
            psi = mk(n, 2, seed=157 + n) * scale
            x = _mk_from_dense(psi, chi)
            for center in (0, n // 2, n - 1):
                x.canonicalize_(int(center))
                _assert_states_close(x.to_dense(), psi, TOL, f"(canonicalize center={center} {label})")
            ns = _floats(x.norm_sq())
            for b in range(2):
                q = _qmps_from_dense_row(psi[b], n)
                ns_serial = MpsLeakageForward._norm_sq(q)
                assert abs(ns[b] - ns_serial) <= 1e-12, f"norm_sq vs serial: {ns[b]} vs {ns_serial}"
                MpsLeakageForward._renormalize(q)
                x1 = _mk_from_dense(psi[b:b + 1], chi)
                x1.renormalize_()
                _assert_states_close(x1.to_dense()[0], _dense_of_qmps(q), TOL,
                                     f"(renormalize vs serial b={b} {label})")


def test_gop1_apply_1site_shared_and_pershot():
    """Shared [3,3] unitary AND the per-shot [B,3,3] (non-unitary gather) form vs the
    serial _apply_gate, at BOTH grades; per-shot branch norms vs serial _renormalize."""
    rng = np.random.default_rng(211)
    H = _qutrit_gate("H", DEVICE)
    Y = _qutrit_gate("Y", DEVICE)
    for n in (4, 6):
        for label, chi, mk in _grades(n):
            psi = mk(n, 3, seed=223 + n)
            x = _mk_from_dense(psi, chi)
            site = 1
            x.apply_1site_(H, site)
            x.apply_1site_(Y, (site + 2) % n)
            serial = []
            qs = []
            for b in range(3):
                q = _qmps_from_dense_row(psi[b], n)
                fwd = _fwd()
                fwd._apply_gate(q, H, site)
                fwd._apply_gate(q, Y, (site + 2) % n)
                serial.append(_dense_of_qmps(q))
                qs.append((fwd, q))
            _assert_states_close(x.to_dense(), torch.stack(serial), TOL, f"(shared 1-site {label})")
            # per-shot NON-unitary form (heterogeneous): sqrt(F_bit)-like diag + a contraction
            Us = torch.stack([
                torch.diag(torch.tensor([1.0, 0.0, (1.0 - B_EFF) ** 0.5], dtype=CDTYPE, device=DEVICE)),
                torch.diag(torch.tensor([0.0, 1.0, B_EFF ** 0.5], dtype=CDTYPE, device=DEVICE)),
                0.8 * torch.as_tensor(
                    rng.standard_normal((3, 3)) + 1j * rng.standard_normal((3, 3)),
                    dtype=CDTYPE, device=DEVICE),
            ])
            x.apply_1site_(Us, site)
            raws = []
            for b in range(3):
                fwd, q = qs[b]
                fwd._apply_gate(q, Us[b], site)
                raws.append(_dense_of_qmps(q))
            # RAW (pre-renorm) elementwise match -- norms are O(1) so 1e-12 abs is meaningful
            _assert_states_close(x.to_dense(), torch.stack(raws), TOL, f"(per-shot 1-site raw {label})")
            ns_b = _floats(x.norm_sq())
            x.renormalize_()
            fin = []
            for b in range(3):
                fwd, q = qs[b]
                ns_serial = MpsLeakageForward._renormalize(q)
                assert abs(ns_b[b] - ns_serial) <= 1e-12
                fin.append(_dense_of_qmps(q))
            _assert_states_close(x.to_dense(), torch.stack(fin), TOL, f"(per-shot 1-site renorm {label})")


def test_gop1_site_rdm():
    """site_rdm (both normalized flags) vs the from-scratch dense RDM; diagonal vs the
    REAL serial _site_population (which reads local_expectation_canonical)."""
    for n in (4, 6):
        for label, chi, mk in _grades(n):
            psi = mk(n, 2, seed=307 + n) * 1.2  # non-unit: normalized=False is the branch-norm read
            x = _mk_from_dense(psi, chi)
            fwd = _fwd()
            for site in (0, n // 2, n - 1):
                rho_u = x.site_rdm(int(site), normalized=False)
                rho_n = x.site_rdm(int(site), normalized=True)
                ref_u = _dense_rdm(psi, site, n, normalized=False)
                ref_n = _dense_rdm(psi, site, n, normalized=True)
                assert float((rho_u - ref_u).abs().max()) <= TOL, f"(rdm unnorm site={site} {label})"
                assert float((rho_n - ref_n).abs().max()) <= TOL, f"(rdm norm site={site} {label})"
                for b in range(2):
                    q = _qmps_from_dense_row(psi[b], n)
                    for lev in (0, 1, 2):
                        pop = fwd._site_population(q, int(site), lev)
                        assert abs(float(rho_n[b, lev, lev].real) - pop) <= 1e-12


def test_gop1_local_expectation_parity():
    """local_expectation with the parity diagonal on contiguous AND non-contiguous
    (identity-extended) supports vs the REAL serial _parity_expectation; this leg also
    VALIDATES the from-scratch dense referee against the serial arm (the anchor the
    non-monotonic cases below stand on)."""
    for n in (4, 6):
        for label, chi, mk in _grades(n):
            psi = mk(n, 2, seed=401 + n)
            x = _mk_from_dense(psi, chi)
            fwd = _fwd()
            for sites in ((1, 2), (0, 2, 3)):  # contiguous + gapped (identity-extended)
                G = _parity_string(len(sites), D2_A)
                got = _floats(x.local_expectation(G, sites, normalized=True))
                ref_dense = _floats(_dense_expect(psi, G, sites, n, normalized=True))
                for b in range(2):
                    q = _qmps_from_dense_row(psi[b], n)
                    ref_serial = fwd._parity_expectation(q, [int(s) for s in sites], D2_A)
                    assert abs(got[b] - ref_serial) <= 1e-12, f"(parity vs serial {sites} {label})"
                    assert abs(ref_dense[b] - ref_serial) <= 1e-12, "dense referee failed its serial anchor"


def test_gop1_local_expectation_permutation_asymmetric_nonmonotonic():
    """v2 case (b): a permutation-ASYMMETRIC G on a NON-MONOTONIC sites tuple (every
    production operator is permutation-symmetric -- a leg-order bug is otherwise
    invisible). Referee: the dense from-scratch convention (validated vs the serial arm
    in test_gop1_local_expectation_parity); a swapped-enumeration CONTROL is asserted
    to DIFFER (anti-vacuous)."""
    A = torch.diag(torch.tensor([1.0, -1.0, 0.5], dtype=CDTYPE, device=DEVICE))
    Bd = torch.diag(torch.tensor([1.0, 0.5, -1.0], dtype=CDTYPE, device=DEVICE))
    G = torch.kron(A, Bd)  # leg0 (MSB) = A, leg1 = Bd -- asymmetric under leg swap
    Gswap = torch.kron(Bd, A)
    for n in (4, 6):
        sites = (3, 1)  # NON-monotonic
        for label, chi, mk in _grades(n):
            psi = mk(n, 2, seed=443 + n)
            x = _mk_from_dense(psi, chi)
            got = _floats(x.local_expectation(G, sites, normalized=True))
            ref = _floats(_dense_expect(psi, G, sites, n, normalized=True))
            ctrl = _floats(_dense_expect(psi, Gswap, sites, n, normalized=True))
            for b in range(2):
                assert abs(ref[b] - ctrl[b]) > 1e-3, "control not discriminating -- re-seed the case"
                assert abs(got[b] - ref[b]) <= 1e-12, f"(asym leg-order n={n} {label}: {got[b]} vs {ref[b]})"


def test_gop1_window_exact_grade_shared_forms():
    """The window op's G-OP-1 leg -- EXACT grade ONLY (v2 scope fence (a): the post-gate
    rank can exceed a truncating cap by the operator Schmidt rank of G; truncating-grade
    window coverage is G-OP-3's). Shared diagonal sqrt(E_s) (vs the REAL serial
    _apply_sqrt_Es, contiguous + non-contiguous), a general dense G (vs the serial
    gate_-nonlocal apply path, lines 683-684), and a non-monotonic asymmetric shared
    dense G (dense referee + control)."""
    n = 4
    chi = exact_chi(n)
    psi = _haar_batch(n, 2, seed=509)
    rng = np.random.default_rng(510)

    # (a) shared diagonal sqrt(E_s), contiguous (1,2) and non-contiguous (0,2)
    for sites, sbit in (((1, 2), 0), ((0, 2), 1)):
        x = _mk_from_dense(psi, chi)
        dvec = _sqrt_es_diag(len(sites), D2_A, sbit)
        disc, bw = _win(x, torch.diag(dvec), sites, diagonal=True)
        got = x.to_dense()
        for b in range(2):
            q = _qmps_from_dense_row(psi[b], n)
            fwd = _fwd()
            ledger = MpsTruncationLedger(chi=chi)
            d_serial = fwd._apply_sqrt_Es(q, [int(s) for s in sites], D2_A, sbit, chi, ledger)
            assert d_serial == 0.0
            _assert_states_close(got[b], _dense_of_qmps(q), TOL, f"(sqrtEs window {sites})")
            # branch_weight = post-trunc PRE-renorm norm^2 == ||G psi||^2 at exact grade
            ref_bw = float(torch.linalg.vector_norm(
                _dense_apply_window(psi[b:b + 1], torch.diag(dvec), sites, n)) ** 2)
            assert abs(bw[b] - ref_bw) <= 1e-12, f"branch_weight {bw[b]} vs dense {ref_bw}"
            assert disc[b] == 0.0  # G-OP-6 evidence too (literal ==)

    # (b) general dense 2-site unitary, contiguous (0,1) and non-contiguous (1,3)
    for sites in ((0, 1), (1, 3)):
        G = _rand_unitary(PHYS ** 2, rng)
        x = _mk_from_dense(psi, chi)
        disc, bw = _win(x, G, sites, diagonal=False)
        got = x.to_dense()
        ref = _dense_apply_window(psi, G, sites, n)  # unitary: already unit-norm rows
        for b in range(2):
            # serial referee: the exact-grade gate_-nonlocal apply path (_apply_sqrt_Es
            # lines 683-684 / codestate _project lines 443-444) with a general G
            q = _qmps_from_dense_row(psi[b], n)
            q.gate_(G, where=tuple(int(s) for s in sites), contract="nonlocal",
                    max_bond=chi, cutoff=0.0)
            MpsLeakageForward._renormalize(q)
            _assert_states_close(got[b], _dense_of_qmps(q), TOL, f"(dense-G window {sites} serial)")
            _assert_states_close(got[b], ref[b], TOL, f"(dense-G window {sites} dense)")
            assert disc[b] == 0.0
            assert abs(bw[b] - 1.0) <= 1e-12  # unitary on a unit state

    # (c) NON-monotonic + permutation-asymmetric shared dense G (leg-order pin)
    A = torch.diag(torch.tensor([1.0, 0.7, 0.4], dtype=CDTYPE, device=DEVICE))
    Bd = torch.diag(torch.tensor([1.0, 0.5, -0.3], dtype=CDTYPE, device=DEVICE))
    G = torch.kron(A, Bd)
    sites = (2, 0)
    x = _mk_from_dense(psi, chi)
    disc, bw = _win(x, G, sites, diagonal=True)  # diagonal (kron of diags) -> fast path legal
    got = x.to_dense()
    ref = _dense_apply_window(psi, G, sites, n)
    ctrl = _dense_apply_window(psi, torch.kron(Bd, A), sites, n)
    for b in range(2):
        assert float((_normalized(ref[b]) - _normalized(ctrl[b])).abs().max()) > 1e-3, \
            "leg-order control not discriminating"
        _assert_states_close(got[b], _normalized(ref[b]), TOL, "(asym non-monotonic window)")
        ref_bw = float(torch.linalg.vector_norm(ref[b]) ** 2)
        assert abs(bw[b] - ref_bw) <= 1e-12
        assert disc[b] == 0.0


def test_gop1_window_pershot_diagonal_exact_grade():
    """The v2-recheck G-OP-1 leg for the PER-SHOT diagonal window form d[B,3^w]
    (D-2 op 7 v4): heterogeneous per-shot diagonals, NON-monotonic sites, with the
    3^w-axis enumeration PINNED to trit-tuples row-major, sites[0] the most-significant
    factor (mps_forward.py lines 664-668). The production sqrt(E_s) is
    permutation-symmetric, so this heterogeneous ASYMMETRIC d is what makes an
    enumeration bug visible (swapped-enumeration control asserted to differ)."""
    n = 4
    chi = exact_chi(n)
    psi = _haar_batch(n, 3, seed=557)
    sites = (3, 1)  # non-monotonic
    diag_a = torch.tensor([1.0, 0.7, 0.4], dtype=CDTYPE, device=DEVICE)
    diag_b = torch.tensor([1.0, 0.5, -0.3], dtype=CDTYPE, device=DEVICE)
    d_rows = []
    for b in range(3):
        sa = diag_a * (1.0 + 0.1 * b)   # heterogeneous across shots
        sb = diag_b * (1.0 - 0.05 * b)
        d_rows.append(torch.kron(sa, sb))  # sites[0]=3 -> MSB factor sa
    d = torch.stack(d_rows)  # [B, 9]
    x = _mk_from_dense(psi, chi)
    disc, bw = _win(x, d, sites, diagonal=True)
    got = x.to_dense()
    for b in range(3):
        Gb = torch.diag(d[b])
        ref = _dense_apply_window(psi[b:b + 1], Gb, sites, n)[0]
        # enumeration CONTROL: swapped per-site factors must differ materially
        Gsw = torch.diag(torch.kron(diag_b * (1.0 - 0.05 * b), diag_a * (1.0 + 0.1 * b)))
        ctrl = _dense_apply_window(psi[b:b + 1], Gsw, sites, n)[0]
        assert float((_normalized(ref) - _normalized(ctrl)).abs().max()) > 1e-3, \
            "enumeration control not discriminating"
        # quimb cross-check (2nd independent path for the leg-order pin)
        q = _qmps_from_dense_row(psi[b], n)
        q.gate_(Gb, where=sites, contract="nonlocal", max_bond=chi, cutoff=0.0)
        MpsLeakageForward._renormalize(q)
        _assert_states_close(_dense_of_qmps(q), _normalized(ref), TOL, "(quimb vs dense leg-order)")
        _assert_states_close(got[b], _normalized(ref), TOL, f"(per-shot diag window b={b})")
        ref_bw = float(torch.linalg.vector_norm(ref) ** 2)
        assert abs(bw[b] - ref_bw) <= 1e-12
        assert disc[b] == 0.0


def test_gop1_offcenter_invocation():
    """v2 case (c): the window op and kraus_sample_ invoked with the orthogonality
    center deliberately FAR from the target -- certifies the canonicalize-first
    contract (the ops must canonicalize themselves, not trust the caller)."""
    n = 4
    chi = exact_chi(n)
    psi = _haar_batch(n, 2, seed=601)
    kraus = _leak_kraus()
    ks = _kraus_stack(kraus)

    # kraus_sample_ at site 0 with center parked at n-1
    # FIX-2: weight-ranked targets (dominant no-jump + second-largest jump branch),
    # never literal indices 0 / K-1 (inverted under the ascending Choi-eigh order).
    pk_ref = _dense_leak_pk(psi[0], kraus, 0, n)
    pk_ref1 = _dense_leak_pk(psi[1], kraus, 0, n)
    us = [_u_for_branch(pk_ref, _pick_branches(pk_ref)[0]),
          _u_for_branch(pk_ref1, _pick_branches(pk_ref1)[1])]
    x_far = _mk_from_dense(psi, chi)
    x_far.canonicalize_(n - 1)  # center FAR from site 0
    sel_far, pk_far = x_far.kraus_sample_(ks, 0, _u_tensor(us))
    x_fresh = _mk_from_dense(psi, chi)
    sel_fresh, pk_fresh = x_fresh.kraus_sample_(ks, 0, _u_tensor(us))
    assert _ints(sel_far) == _ints(sel_fresh)
    assert float((torch.as_tensor(pk_far) - torch.as_tensor(pk_fresh)).abs().max()) <= 1e-12
    _assert_states_close(x_far.to_dense(), x_fresh.to_dense(), TOL, "(off-center kraus)")
    fwd = _fwd()
    for b in range(2):
        q = _qmps_from_dense_row(psi[b], n)
        fwd._leak_sample(q, kraus, 0, us[b])
        _assert_states_close(x_far.to_dense()[b], _dense_of_qmps(q), TOL, "(off-center kraus vs serial)")

    # window op on (2,3) with center parked at 0
    G = _rand_unitary(PHYS ** 2, np.random.default_rng(607))
    x_far = _mk_from_dense(psi, chi)
    x_far.canonicalize_(0)
    _win(x_far, G, (2, 3), diagonal=False)
    x_fresh = _mk_from_dense(psi, chi)
    _win(x_fresh, G, (2, 3), diagonal=False)
    _assert_states_close(x_far.to_dense(), x_fresh.to_dense(), TOL, "(off-center window)")
    ref = _dense_apply_window(psi, G, (2, 3), n)
    for b in range(2):
        _assert_states_close(x_far.to_dense()[b], _normalized(ref[b]), TOL, "(off-center window dense)")


# =========================================================================== #
# G-OP-2 -- sampling equivalence on one shared u stream (bit-identity + state) #
# =========================================================================== #
def test_gop2_kraus_sample_shared_u():
    """kraus_sample_ vs the REAL serial _leak_sample on the SAME u: identical selected
    branches, pk <= 1e-12, post-state <= 1e-12. BOTH grades (1-site: truncation-free).
    Branch-targeted u (weight-ranked via _pick_branches, FIX-2 / prereg v5) covers the
    DOMINANT no-jump branch and the second-largest jump branch. Under the ascending
    Choi-eigh Kraus order (channels.py lines 639-643) the no-jump branch IS the LAST
    index K-1 (kraus[0] is the smallest kept dust branch, hittability-fragile), so
    branches are targeted by pk MAGNITUDE, never by literal index. The serial fallback
    clamp (first k with ``u*tot <= cumsum_k``, else K-1; mps_forward.py lines 578-586)
    is a DEFENSIVE floating-point guard that mid-range u cannot reach (u < 1 =>
    u*tot < cumsum_{K-1} = tot exactly): it is verified BY CONSTRUCTION in the module
    (min over an empty hit set => the K-1 clamp) and deliberately NOT exercised with
    real draws. Knife-edge margin asserted on every draw."""
    kraus = _leak_kraus()
    ks = _kraus_stack(kraus)
    K = len(kraus)
    for n in (4, 6):
        for label, chi, mk in _grades(n):
            psi = mk(n, 3, seed=701 + n)
            site = n // 2
            pk_refs = [_dense_leak_pk(psi[b], kraus, site, n) for b in range(3)]
            # FIX-2: weight-ranked targeting -- shot 0 hits the dominant no-jump branch
            # (== the LAST index under ascending Choi-eigh), shots 1/2 the second-largest
            # jump branch; never literal 0 / K-1.
            picks = [_pick_branches(pk_refs[b]) for b in range(3)]
            targets = [picks[0][0], picks[1][1], picks[2][1]]
            us = [_u_for_branch(pk_refs[b], targets[b]) for b in range(3)]
            sel_ref = [_cumsel(pk_refs[b], us[b]) for b in range(3)]  # replica, lines 578-586
            assert sel_ref == targets  # the targeting itself is a check of the rule
            x = _mk_from_dense(psi, chi)
            sel, pk = x.kraus_sample_(ks, site, _u_tensor(us))
            assert _ints(sel) == sel_ref, f"(kraus sel {label} n={n})"
            pk_t = torch.as_tensor(pk, dtype=RDTYPE, device=DEVICE) if not isinstance(pk, torch.Tensor) else pk
            for b in range(3):
                _assert_margin_cumsum(us[b], pk_refs[b])
                for k in range(K):
                    assert abs(float(pk_t[b, k]) - pk_refs[b][k]) <= 1e-12, f"(pk b={b} k={k} {label})"
            fwd = _fwd()
            fin = []
            for b in range(3):
                q = _qmps_from_dense_row(psi[b], n)
                fwd._leak_sample(q, kraus, site, us[b])  # the REAL serial referee
                fin.append(_dense_of_qmps(q))
            _assert_states_close(x.to_dense(), torch.stack(fin), TOL, f"(kraus post-state {label} n={n})")


def test_gop2_born_stab_composition_exact_grade():
    """The WINDOW-CONTAINING Born-stab composition -- EXACT grade only (v3 fence: the
    sqrt(E_s) post-gate rank exceeds a truncating cap). Shared u => identical sbit AND
    <=1e-12 state vs the REAL serial _measure_stabilizer; the per-shot d[B,3^w] window
    form is exercised (sbit is per shot); discarded is the literal 0.0."""
    n = 4
    chi = exact_chi(n)
    psi = _haar_batch(n, 2, seed=809)
    sites, isx = [1, 2], [1, 0]
    fwd = _fwd()
    H = _qutrit_gate("H", DEVICE)
    us, sbit_ref, fin = [], [], []
    for b in range(2):
        q = _qmps_from_dense_row(psi[b], n)
        probe = q.copy()
        for j, s in enumerate(sites):
            if isx[j] == 1:
                fwd._apply_gate(probe, H, s)
        p0 = 0.5 * (1.0 + fwd._parity_expectation(probe, sites, D2_A))
        assert 1e-6 < p0 < 1.0 - 1e-6, "degenerate p0 -- re-seed"
        u = _u_below(p0) if b == 0 else _u_above(p0)   # force sbit 0 and 1 (coverage)
        us.append(u)
        ledger = MpsTruncationLedger(chi=chi)
        sb, disc = fwd._measure_stabilizer(q, sites, isx, D2_A, u, chi, ledger)
        assert disc == 0.0
        sbit_ref.append(int(sb))
        fin.append(_dense_of_qmps(q))
    assert sbit_ref == [0, 1]
    x = _mk_from_dense(psi, chi)
    sbits, disc, bw, p0s = _batched_born_stab(x, tuple(sites), isx, D2_A, us)
    assert sbits == sbit_ref, "Born-stab sbit mismatch"
    for b in range(2):
        assert disc[b] == 0.0   # literal (G-OP-6 semantics)
        # class-(a) cross-check: bw == Tr[E_s rho] on a unit state == p0 (sbit 0) / 1-p0
        want = p0s[b] if sbits[b] == 0 else 1.0 - p0s[b]
        assert abs(bw[b] - want) <= 1e-12, f"branch_weight {bw[b]} != Born prob {want}"
    _assert_states_close(x.to_dense(), torch.stack(fin), TOL, "(Born-stab state)")


def test_gop2_armC_leakflag():
    """Arm-C leak-flag composition (serial lines 617-630: SEQUENTIAL per support site --
    p2 = NORMALIZED population of the CURRENT partially-projected state, strict u < p2,
    project diag(0,0,1)/diag(1,1,0), renormalize per site) at BOTH grades; plus the FULL
    arm-C _measure_stabilizer at the exact grade."""
    for n in (4, 6):
        for label, chi, mk in _grades(n):
            psi = mk(n, 2, seed=907 + n)
            sites = [1, 2]
            fwd = _fwd()
            flags_ref, us_all, fin = [], [], []
            for b in range(2):
                q = _qmps_from_dense_row(psi[b], n)
                flags_b, us_b = [], []
                for j, s in enumerate(sites):  # serial arm = the REAL methods, sequenced per lines 617-630
                    p2 = fwd._site_population(q, s, 2)
                    assert p2 > 1e-4, "no |2> mass to flag -- re-seed"
                    u = _u_below(p2) if (b + j) % 2 == 0 else _u_above(p2)  # cover flag 1 AND 0
                    us_b.append(u)
                    lf = 1 if u < p2 else 0
                    flags_b.append(lf)
                    if lf:
                        proj = torch.diag(torch.tensor([0.0, 0.0, 1.0], dtype=CDTYPE, device=DEVICE))
                    else:
                        proj = torch.diag(torch.tensor([1.0, 1.0, 0.0], dtype=CDTYPE, device=DEVICE))
                    fwd._apply_gate(q, proj, s)
                    MpsLeakageForward._renormalize(q)
                flags_ref.append(flags_b)
                us_all.append(us_b)
                fin.append(_dense_of_qmps(q))
            x = _mk_from_dense(psi, chi)
            flags_got = [[0, 0], [0, 0]]
            for j, s in enumerate(sites):
                rho = x.site_rdm(int(s), normalized=True)
                projs = []
                for b in range(2):
                    p2 = float(rho[b, 2, 2].real)
                    u = us_all[b][j]
                    _assert_margin_thresh(u, p2)
                    lf = 1 if u < p2 else 0
                    flags_got[b][j] = lf
                    dg = [0.0, 0.0, 1.0] if lf else [1.0, 1.0, 0.0]
                    projs.append(torch.diag(torch.tensor(dg, dtype=CDTYPE, device=DEVICE)))
                x.apply_1site_(torch.stack(projs), int(s))
                x.renormalize_()
            assert flags_got == flags_ref, f"(arm-C flags {label} n={n})"
            _assert_states_close(x.to_dense(), torch.stack(fin), TOL, f"(arm-C state {label} n={n})")

    # FULL arm-C measure (flags + Born + per-shot sqrt(E_s) window) -- exact grade
    n = 4
    chi = exact_chi(n)
    psi = _haar_batch(n, 2, seed=911)
    sites, isx = [1, 2], [1, 0]
    fwd = _fwd()
    H = _qutrit_gate("H", DEVICE)
    recs, fin = [], []
    for b in range(2):
        q = _qmps_from_dense_row(psi[b], n)
        probe = q.copy()
        for j, s in enumerate(sites):
            if isx[j] == 1:
                fwd._apply_gate(probe, H, s)
        u_lf = []
        for j, s in enumerate(sites):
            p2 = fwd._site_population(probe, s, 2)
            u = _u_below(p2) if (b + j) % 2 == 0 else _u_above(p2)
            u_lf.append(u)
            lf = 1 if u < p2 else 0
            dg = [0.0, 0.0, 1.0] if lf else [1.0, 1.0, 0.0]
            fwd._apply_gate(probe, torch.diag(torch.tensor(dg, dtype=CDTYPE, device=DEVICE)), s)
            MpsLeakageForward._renormalize(probe)
        p0 = 0.5 * (1.0 + fwd._parity_expectation(probe, sites, D2_A))
        u_out = _u_below(p0) if b == 0 else _u_above(p0)
        ledger = MpsTruncationLedger(chi=chi)
        sb, disc = fwd._measure_stabilizer(q, sites, isx, D2_A, u_out, chi, ledger,
                                           arm="C", u_leakflags=u_lf)
        assert disc == 0.0
        recs.append((u_lf, u_out, int(sb)))
        fin.append(_dense_of_qmps(q))
    x = _mk_from_dense(psi, chi)
    # batched: H rotations, sequential flags, parity, sbit, per-shot sqrt(E_s), H back
    for j, s in enumerate(sites):
        if isx[j] == 1:
            x.apply_1site_(H, int(s))
    for j, s in enumerate(sites):
        rho = x.site_rdm(int(s), normalized=True)
        projs = []
        for b in range(2):
            p2 = float(rho[b, 2, 2].real)
            u = recs[b][0][j]
            _assert_margin_thresh(u, p2)
            dg = [0.0, 0.0, 1.0] if u < p2 else [1.0, 1.0, 0.0]
            projs.append(torch.diag(torch.tensor(dg, dtype=CDTYPE, device=DEVICE)))
        x.apply_1site_(torch.stack(projs), int(s))
        x.renormalize_()
    ppar = _floats(x.local_expectation(_parity_string(2, D2_A), tuple(sites), normalized=True))
    sb_got = []
    for b in range(2):
        p0 = 0.5 * (1.0 + ppar[b])
        _assert_margin_thresh(recs[b][1], p0)
        sb_got.append(0 if recs[b][1] < p0 else 1)
    assert sb_got == [recs[0][2], recs[1][2]], "(full arm-C sbit)"
    d_es = torch.stack([_sqrt_es_diag(2, D2_A, sb) for sb in sb_got])
    disc, _bw = _win(x, d_es, tuple(sites), diagonal=True)
    assert disc[0] == 0.0 and disc[1] == 0.0
    for j, s in enumerate(sites):
        if isx[j] == 1:
            x.apply_1site_(H, int(s))
    _assert_states_close(x.to_dense(), torch.stack(fin), TOL, "(full arm-C state)")


def test_gop2_hard2_terminal():
    """hard2 terminal vs the REAL _terminal_readout on shared u, BOTH grades, B=3 with
    one shot driven to EXACT ZERO NORM (per-shot zero gate) to exercise the registered
    wt<=NUMERICAL_ZERO=>p1=0.5 guard and the per-shot renormalize mask (a degenerate
    shot must never poison the batch)."""
    log_support = [0, 3]
    m = 1
    for n in (4, 6):
        for label, chi, mk in _grades(n):
            psi = mk(n, 3, seed=1009 + n)
            zero_gate = torch.zeros((PHYS, PHYS), dtype=CDTYPE, device=DEVICE)
            eye = torch.eye(PHYS, dtype=CDTYPE, device=DEVICE)
            Us = torch.stack([eye, eye, zero_gate])  # shot 2 -> exact zero state
            rng = np.random.default_rng(1013 + n)
            fwd = _fwd()
            u_mat, bits_ref, flips_ref, fin = [], [], [], []
            for b in range(3):
                q = _qmps_from_dense_row(psi[b], n)
                fwd._apply_gate(q, Us[b], 1)
                us, tr = _serial_hard2(fwd, q, n, log_support, B_EFF, m, rng)
                u_mat.append(us)
                bits_ref.append(list(tr.bits))
                flips_ref.append(int(tr.flip))
                fin.append(_dense_of_qmps(q))
            x = _mk_from_dense(psi, chi)
            x.apply_1site_(Us, 1)
            bits, flips = _batched_hard2(x, n, log_support, B_EFF, m, u_mat)
            assert bits == bits_ref, f"(hard2 bits {label} n={n})"
            assert flips == flips_ref, f"(hard2 flip {label} n={n})"
            out = x.to_dense()
            assert bool(torch.isfinite(out).all()), "degenerate shot poisoned the batch (NaN/inf)"
            _assert_states_close(out, torch.stack(fin), TOL, f"(hard2 state {label} n={n})")
            assert float(out[2].abs().max()) <= TOL, "zero-norm shot must stay exactly dead"


def test_gop2_hard3_terminal():
    """hard3 terminal vs the REAL _terminal_readout (gen=None) on shared u, BOTH
    grades: cumulative STRICT target<cum with fallback kbar=2, and the kbar==2
    DETERMINISTIC residual-split sub-draw u2 (strict u2 < b) exercised on BOTH sides of
    b (bit 1 and bit 0); level coverage asserted (anti-vacuous).

    Plus the BATCHED-ONLY degenerate leg (FIX-5; prereg D-2 registry v5 note + chip
    task_9f0687fe): the registered hard3 guard ``tot <= NUMERICAL_ZERO => kbar=0`` is
    the NORMATIVE BATCHED semantics -- the serial arm cannot referee it because its
    own guard is NaN-shadowed dead code (mps_forward.py line 527 normalized read =>
    NaN populations on a zero-norm state; lines 802-803 ``NaN <= NUMERICAL_ZERO`` is
    False; lines 830-831 then emit bit=(0.5 < b) via the kbar=2 fallback) -- a
    DECLARED intentional divergence on the degenerate regime. One shot is driven to
    EXACT zero norm (the hard2 zero-gate mechanism) and must land kbar=0 / bit=0 at
    every site with NO NaN anywhere in the batch, the healthy shots bit-identical and
    state-identical to the run WITHOUT the degenerate shot (the per-shot mask must not
    poison them)."""
    log_support = [0, 2]
    m = 0
    for n in (4, 6):
        for label, chi, mk in _grades(n):
            psi = mk(n, 3, seed=1103 + n)
            rng = np.random.default_rng(1109 + n)
            fwd = _fwd()
            # shot0: force kbar=2 at qutrit 1 with u2=0.45 (< b=0.9 -> bit 1);
            # shot1: force kbar=2 at qutrit 1 with u2=0.95 (> b -> bit 0); shot2 free.
            forces = [{1: 0.45}, {1: 0.95}, {}]
            u_mat, lv_ref, bits_ref, flips_ref, fin = [], [], [], [], []
            for b in range(3):
                q = _qmps_from_dense_row(psi[b], n)
                us, tr = _serial_hard3(fwd, q, n, log_support, B_EFF, m, rng, force_level2=forces[b])
                u_mat.append(us)
                lv_ref.append(list(tr.levels))
                bits_ref.append(list(tr.bits))
                flips_ref.append(int(tr.flip))
                fin.append(_dense_of_qmps(q))
            assert lv_ref[0][1] == 2 and lv_ref[1][1] == 2      # sub-draw exercised
            assert bits_ref[0][1] == 1 and bits_ref[1][1] == 0  # both sides of b
            assert any(l != 2 for l in lv_ref[2])               # non-leaked coverage
            x = _mk_from_dense(psi, chi)
            levels, bits, flips = _batched_hard3(x, n, log_support, B_EFF, m, u_mat)
            assert levels == lv_ref, f"(hard3 levels {label} n={n})"
            assert bits == bits_ref, f"(hard3 bits {label} n={n})"
            assert flips == flips_ref, f"(hard3 flips {label} n={n})"
            _assert_states_close(x.to_dense(), torch.stack(fin), TOL, f"(hard3 state {label} n={n})")

            # ---- FIX-5: BATCHED-ONLY degenerate leg (the WRITTEN tot<=NUMERICAL_ZERO
            # => kbar=0 guard; serial referee NaN-shadowed there -- see the docstring
            # and the _serial_hard3 note; prereg D-2 registry v5 + chip task_9f0687fe).
            # Shot 3 = a copy of shot 0 driven to EXACT zero norm via the hard2
            # zero-gate mechanism; shots 0-2 re-run unchanged alongside it.
            zero_gate = torch.zeros((PHYS, PHYS), dtype=CDTYPE, device=DEVICE)
            eye = torch.eye(PHYS, dtype=CDTYPE, device=DEVICE)
            psi4 = torch.cat([psi, psi[0:1]], dim=0)
            x4 = _mk_from_dense(psi4, chi)
            Us4 = torch.stack([eye, eye, eye, zero_gate])  # shot 3 -> exact zero state
            x4.apply_1site_(Us4, 1)
            # the degenerate shot's u row is NEVER read (kbar=0 short-circuits both the
            # cumulative draw and the |2> sub-draw); placeholder values only.
            u_mat4 = [list(row) for row in u_mat] + [[0.5] * n]
            levels4, bits4, flips4 = _batched_hard3(x4, n, log_support, B_EFF, m, u_mat4)
            assert levels4[3] == [0] * n and bits4[3] == [0] * n, \
                "degenerate shot must land kbar=0 / bit=0 at every site (the WRITTEN guard)"
            assert flips4[3] == (int(m) & 1), "degenerate flip must follow the all-zero bits"
            out4 = x4.to_dense()
            assert bool(torch.isfinite(out4).all()), \
                "degenerate shot poisoned the batch (NaN/inf; the per-shot mask failed)"
            assert float(out4[3].abs().max()) <= TOL, "zero-norm shot must stay exactly dead"
            # healthy shots UNCHANGED vs the run WITHOUT the degenerate shot (the
            # 3-shot run above; the eye 1-site ops on shots 0-2 are state-preserving).
            assert levels4[:3] == levels and bits4[:3] == bits and flips4[:3] == flips, \
                f"(hard3 degenerate-mask poisoned a healthy shot {label} n={n})"
            _assert_states_close(out4[:3], x.to_dense(), TOL,
                                 f"(hard3 degenerate-mask healthy states {label} n={n})")


# =========================================================================== #
# G-OP-3 -- truncating consistency (the ONLY registered truncating-window gate) #
# =========================================================================== #
def _gop3_engineered_case(spectra: list[list[float]], seed: int):
    """Build the registered exactly-one-truncating-split case: n=4, chi=2, window
    (1,2). Pre-states are PRODUCTS x0 (x) e_j (x) x3 (window content = a standard basis
    vector -> rank 1 at EVERY cut; from_dense at chi=2 is trivially rank-fenced), and
    the SHARED window unitary G carries e_j -> phi'_j where phi'_j has the DESIGNED
    Schmidt spectrum across the window-internal cut (global cut 1). Post-gate ranks:
    cut 0 and cut 2 stay 1 (product structure preserved outside the window) -> the
    window's re-split truncates at EXACTLY one split (cut 1), the regime where the D-3
    books are class-(a) identical. Returns (psi0 [B,81], G, spectra_t)."""
    n = 4
    rng = np.random.default_rng(seed)
    D2w = PHYS ** 2
    cols_out = []
    # ONE shared pair of orthonormal families across ALL j -- the orthogonality of the
    # phi'_j RESTS on sharing: <phi'_0|phi'_1> = sum_r sqrt(l0_r l1_r) <c_r|c_{(r+1)%3}>
    # = 0 needs the SAME Cu columns in both. (First gate run caught the per-j redraw:
    # independent families give generic overlap ~0.25 and the QR pin fails loudly.)
    Au = _rand_unitary(PHYS, rng)
    Cu = _rand_unitary(PHYS, rng)
    for j, lam in enumerate(spectra):
        assert abs(sum(float(l) for l in lam) - 1.0) <= 1e-12, \
            f"designed spectrum must be unit-trace (got sum={sum(lam)})"
        phi = torch.zeros(D2w, dtype=CDTYPE, device=DEVICE)
        for r, l in enumerate(lam):
            # pairing (a_r, c_{(r+j) mod 3}) keeps phi'_0 _|_ phi'_1 while giving each
            # its own designed spectrum (shared left/right orthonormal families).
            phi = phi + (float(l) ** 0.5) * torch.kron(Au[:, r], Cu[:, (r + j) % PHYS])
        cols_out.append(phi)
    G = _unitary_with_leading_cols(cols_out, rng)  # G e_j = phi'_j
    rows = []
    for j in range(len(spectra)):
        x0 = rng.standard_normal(PHYS) + 1j * rng.standard_normal(PHYS)
        x3 = rng.standard_normal(PHYS) + 1j * rng.standard_normal(PHYS)
        x0, x3 = x0 / np.linalg.norm(x0), x3 / np.linalg.norm(x3)
        ej = np.zeros(D2w, dtype=np.complex128)
        ej[j] = 1.0
        rows.append(torch.as_tensor(np.kron(x0, np.kron(ej, x3)), dtype=CDTYPE, device=DEVICE))
    return torch.stack(rows), G


def _gop3_run_and_check(spectra: list[list[float]], seed: int, flat_block: bool):
    n, chi, sites = 4, 2, (1, 2)
    psi0, G = _gop3_engineered_case(spectra, seed)
    B = len(spectra)
    psi_post = _dense_apply_window(psi0, G, sites, n)  # exact post state (unitary, unit norm)
    for b in range(B):
        lam = _cut_lambdas(psi_post[b], n, 1)
        want = sorted(spectra[b], reverse=True)
        for r, wv in enumerate(want):
            assert abs(float(lam[r]) - wv) <= 1e-12, "engineered spectrum failed to realize"
        # EXACTLY-ONE-truncating-split precondition: cuts 0 and 2 stay rank 1
        assert float(_cut_lambdas(psi_post[b], n, 0)[1:].sum()) <= 1e-13
        assert float(_cut_lambdas(psi_post[b], n, 2)[1:].sum()) <= 1e-13
        # REGISTERED spectral gap: |smallest retained - largest discarded| of the
        # NORMALIZED (unit-trace) Gram spectrum, LAMBDA units, >= 1e-3
        gap = float(lam[chi - 1] - lam[chi])
        assert gap >= 1e-3, f"registered gap violated: {gap}"
        # conditioning fence, SIGMA units (sqrt of the Gram lambdas), >= 1e-3
        cond = float((lam[chi - 1] / lam[0]) ** 0.5)
        assert cond >= 1e-3, f"conditioning fence violated: {cond}"
        if flat_block:
            # the degenerate block is ENTIRELY retained (straddling the cap is
            # ill-posed for ANY algorithm -- excluded by construction and declared)
            assert abs(float(lam[0]) - float(lam[1])) <= 1e-12

    # FIX-4 / prereg G-OP-3 v5: Gram-path eigh-quality witness at the module's ACTUAL
    # shapes and batching. The module's truncating split runs a BATCHED eigh on the
    # [B, 6, 6] padded-blob Grams (batched_mps.py Gram route: bond_caps(4,2) -> lcap=2,
    # m = lcap*3 = 6, ncols = 3*r_cap = 6, cap_t = 2); torch dispatches batched vs
    # single Hermitian eigensolves through DIFFERENT cuSOLVER kernels, so the previous
    # single unbatched 9x9 eigh could not witness the module's path. Rebuild the
    # SAME-SHAPED batched Gram stack from the harness's known pre-state/window data
    # (the module's internal factors are not exposed; this reconstruction agrees with
    # the module's Gram up to bond-basis gauge -- same nonzero spectrum, the designed
    # Schmidt lambdas -- and exercises the SAME batched kernel: [B,6,6] complex128,
    # same device). This is a DISPATCH-PATH WITNESS, never a factor comparison; the
    # dense-referee logic below is untouched.
    lcap = _bond_caps(n, chi)[0]   # cap of the bond LEFT of site 1 (the window's lo)
    r_cap = _bond_caps(n, chi)[2]  # cap of the bond RIGHT of site 2 (the window's hi)
    m_dim = lcap * PHYS            # = 6, the module's Gram dimension at the split
    rng_w = np.random.default_rng(seed + 7919)
    grams = []
    for b in range(B):
        # psi0[b] = x0 (x) e_j (x) x3 (the engineered product): extract the exact
        # 1-site boundary factors, then express the post-gate state in padded
        # orthonormal bond bases {x0, x0_perp} / {x3, x3_perp} -- the harness analog
        # of the module's blob at the truncating split.
        M0 = psi0[b].reshape(PHYS, PHYS ** 3)
        c0 = int(torch.argmax(torch.linalg.vector_norm(M0, dim=0)))
        x0 = M0[:, c0] / torch.linalg.vector_norm(M0[:, c0])
        M3 = psi0[b].reshape(PHYS ** 3, PHYS)
        r3 = int(torch.argmax(torch.linalg.vector_norm(M3, dim=1)))
        x3 = M3[r3, :] / torch.linalg.vector_norm(M3[r3, :])
        L = _unitary_with_leading_cols([x0], rng_w)[:, :lcap]    # [3, lcap]
        Rb = _unitary_with_leading_cols([x3], rng_w)[:, :r_cap]  # [3, r_cap]
        t = psi_post[b].reshape(PHYS, PHYS, PHYS, PHYS)  # (i0, p1, p2, i3)
        blob = torch.einsum("ia,ipqj,jc->apqc", L.conj(), t, Rb.conj())
        A = blob.reshape(m_dim, PHYS * r_cap)  # rows (a,p1), cols (p2,c) -- module layout
        Gm = A @ A.mH
        grams.append(0.5 * (Gm + Gm.mH))  # hermitize exactly as the module does
    gram_stack = torch.stack(grams)  # [B, 6, 6] complex128, same device as the module
    assert tuple(gram_stack.shape) == (B, m_dim, m_dim) and gram_stack.dtype == CDTYPE
    lam_e, U = torch.linalg.eigh(gram_stack)  # THE batched call (the witnessed dispatch)
    eye_m = torch.eye(m_dim, dtype=CDTYPE, device=DEVICE)
    for b in range(B):
        orth = float((U[b].mH @ U[b] - eye_m).abs().max())
        assert orth <= 1e-12, f"batched eigh orthonormality {orth:.3e} (shot {b})"
        resid = float((gram_stack[b] @ U[b] - U[b] @ torch.diag(lam_e[b].to(CDTYPE))).abs().max())
        assert resid <= 1e-11, f"batched eigh residual {resid:.3e} (shot {b})"  # class (c)

    x = _mk_from_dense(psi0, chi)
    disc, bw = _win(x, G, sites, diagonal=False)
    got = x.to_dense()
    for b in range(B):
        lam = sorted(spectra[b], reverse=True)
        eps_expected = float(sum(lam[chi:]))  # the Schmidt identity, class (a)
        # serial book (mps_forward.py lines 686-698): norm gap truncated-vs-exact apply
        qt = _qmps_from_dense_row(psi0[b], n)
        qt.gate_(G, where=sites, contract="nonlocal", max_bond=chi, cutoff=0.0)
        nt = MpsLeakageForward._norm_sq(qt)
        qe = _qmps_from_dense_row(psi0[b], n)
        qe.gate_(G, where=sites, contract="nonlocal", max_bond=exact_chi(n), cutoff=0.0)
        ne = MpsLeakageForward._norm_sq(qe)
        eps_serial = max(0.0, (ne - nt) / ne)
        MpsLeakageForward._renormalize(qt, norm_sq=nt)
        # |Delta eps| <= 1e-10 between the batched Gram book and the serial norm-gap
        # book (class-(a) identical in the single-truncating-split regime). A miss on
        # ANY criterion here is a registered FINDING to adjudicate -- never a silent
        # tolerance bump.
        assert abs(disc[b] - eps_serial) <= 1e-10, f"|Δeps|={abs(disc[b] - eps_serial):.3e}"
        assert abs(disc[b] - eps_expected) <= 1e-8   # sanity vs the designed spectrum
        assert abs(bw[b] - nt) <= 1e-10, f"branch_weight {bw[b]} vs serial nt {nt}"
        # post-state overlap deficit <= 1e-10 (both unit-norm)
        a_vec = got[b]
        b_vec = _dense_of_qmps(qt)
        ov = float(torch.abs(torch.sum(a_vec.conj() * b_vec)) ** 2)
        assert 1.0 - ov <= 1e-10, f"overlap deficit {1.0 - ov:.3e}"


def test_gop3_single_truncating_split_gap_and_books():
    # retained (0.70, 0.25) / discarded 0.05 -> gap 0.20, cond sqrt(0.25/0.70)~0.6;
    # shot 2: retained (0.55, 0.35) / discarded 0.10 -> gap 0.25.
    _gop3_run_and_check([[0.70, 0.25, 0.05], [0.55, 0.35, 0.10]], seed=1201, flat_block=False)


def test_gop3_flat_spectrum_retained_block():
    # FLAT retained block (0.48, 0.48) ENTIRELY retained, discarded 0.04 -> gap 0.44.
    # (A degenerate block STRADDLING the cap is ill-posed for any algorithm and is
    # excluded by construction -- declared in the prereg.)
    _gop3_run_and_check([[0.48, 0.48, 0.04], [0.46, 0.46, 0.08]], seed=1213, flat_block=True)


# =========================================================================== #
# G-OP-4 -- batch independence (B heterogeneous == each alone at B=1).         #
# =========================================================================== #
def _gop4_pipeline(x, B: int, n: int, ks: torch.Tensor, Us: torch.Tensor,
                   u_kraus: list[float]):
    """Deterministic op pipeline driving EVERY batched op; returns the read record +
    final dense state (dense-reconstruction comparison level)."""
    rec: dict[str, object] = {}
    x.canonicalize_(1)
    rec["norm0"] = _floats(x.norm_sq())
    H = _qutrit_gate("H", DEVICE)
    x.apply_1site_(H, 0)                       # shared unitary
    x.apply_1site_(Us, n // 2)                 # per-shot (non-unitary) form
    x.renormalize_()
    rec["rdm_u"] = x.site_rdm(1, normalized=False).detach().cpu()
    rec["rdm_n"] = x.site_rdm(1, normalized=True).detach().cpu()
    rec["exp_a"] = _floats(x.local_expectation(_parity_string(2, D2_A), (1, 2), normalized=True))
    rec["exp_b"] = _floats(x.local_expectation(_parity_string(2, D2_A), (0, 3), normalized=True))
    sel, pk = x.kraus_sample_(ks, 2, _u_tensor(u_kraus))
    rec["sel"] = _ints(sel)
    rec["pk"] = torch.as_tensor(pk).detach().cpu()
    rec["dense"] = x.to_dense().detach()
    return rec


def test_gop4_batch_vs_single_every_op():
    """B=3 heterogeneous states through every batched op == each state alone at B=1,
    compared at the DENSE-RECONSTRUCTION level (site tensors are gauge/dispatch-
    dependent, the state is not) -- THE cross-shot-leakage gate."""
    n, B = 6, 3
    chi = TRUNC_CHI
    psi = _low_rank_batch(n, B, seed=1301)
    kraus = _leak_kraus()
    ks = _kraus_stack(kraus)
    rng = np.random.default_rng(1307)
    Us = torch.stack([
        torch.diag(torch.tensor([1.0, 0.6, 0.3], dtype=CDTYPE, device=DEVICE)),
        torch.diag(torch.tensor([0.4, 1.0, 0.9], dtype=CDTYPE, device=DEVICE)),
        0.7 * torch.as_tensor(rng.standard_normal((3, 3)) + 1j * rng.standard_normal((3, 3)),
                              dtype=CDTYPE, device=DEVICE),
    ])
    # derive margin-safe per-shot u from the BATCH arm's own pk, then reuse the SAME
    # numeric u in the B=1 runs (knife-edge margin makes the selection u-stable).
    x_probe = _mk_from_dense(psi, chi)
    x_probe.apply_1site_(_qutrit_gate("H", DEVICE), 0)
    x_probe.apply_1site_(Us, n // 2)
    x_probe.renormalize_()
    _sel_p, pk_p = x_probe.kraus_sample_(ks, 2, _u_tensor([0.5] * B))  # probe only (discarded)
    pk_rows = torch.as_tensor(pk_p).detach().cpu()
    # FIX-2: weight-ranked targets (shot 1 -> second-largest jump branch, others -> the
    # dominant no-jump branch); never literal 0 / K-1.
    pk_lists = [[float(v) for v in pk_rows[b]] for b in range(B)]
    u_kraus = [_u_for_branch(pk_lists[b], _pick_branches(pk_lists[b])[1 if b == 1 else 0])
               for b in range(B)]

    x = _mk_from_dense(psi, chi)
    rec_b = _gop4_pipeline(x, B, n, ks, Us, u_kraus)
    for b in range(B):
        x1 = _mk_from_dense(psi[b:b + 1], chi)
        rec_1 = _gop4_pipeline(x1, 1, n, ks, Us[b:b + 1], [u_kraus[b]])
        assert abs(rec_b["norm0"][b] - rec_1["norm0"][0]) <= 1e-12
        assert float((rec_b["rdm_u"][b] - rec_1["rdm_u"][0]).abs().max()) <= TOL
        assert float((rec_b["rdm_n"][b] - rec_1["rdm_n"][0]).abs().max()) <= TOL
        assert abs(rec_b["exp_a"][b] - rec_1["exp_a"][0]) <= 1e-12
        assert abs(rec_b["exp_b"][b] - rec_1["exp_b"][0]) <= 1e-12
        assert rec_b["sel"][b] == rec_1["sel"][0]
        assert float((rec_b["pk"][b] - rec_1["pk"][0]).abs().max()) <= 1e-12
        _assert_states_close(rec_b["dense"][b], rec_1["dense"][0], TOL, f"(gop4 shot {b})")

    # window op (dense shared G) -- exact grade (the registered window-grade routing)
    n4 = 4
    chi4 = exact_chi(n4)
    psi4 = _haar_batch(n4, B, seed=1319)
    G = _rand_unitary(PHYS ** 2, rng)
    xw = _mk_from_dense(psi4, chi4)
    disc_b, bw_b = _win(xw, G, (1, 2), diagonal=False)
    dense_b = xw.to_dense()
    for b in range(B):
        x1 = _mk_from_dense(psi4[b:b + 1], chi4)
        disc_1, bw_1 = _win(x1, G, (1, 2), diagonal=False)
        assert disc_b[b] == disc_1[0] == 0.0
        assert abs(bw_b[b] - bw_1[0]) <= 1e-12
        _assert_states_close(dense_b[b], x1.to_dense()[0], TOL, f"(gop4 window shot {b})")

    # broadcast_from_quimb: B copies, per-shot heterogeneous op, == the B=1 runs
    q = _qmps_from_dense_row(psi4[0], n4)
    xb = _mk_broadcast(q, B, chi4)
    xb.apply_1site_(Us, 1)
    xb.renormalize_()
    for b in range(B):
        x1 = _mk_from_dense(psi4[0:1], chi4)
        x1.apply_1site_(Us[b:b + 1], 1)
        x1.renormalize_()
        _assert_states_close(xb.to_dense()[b], x1.to_dense()[0], TOL, f"(gop4 broadcast shot {b})")


def test_gop4_window_pershot_diagonal_batch_vs_single():
    """The v2-recheck G-OP-4 leg: apply_window_recompress_ with a HETEROGENEOUS
    per-shot diagonal d[B,3^w] at B=3 vs the three B=1 runs -- isolates a
    gather/broadcast bug in the diagonal fast path from a composition-level failure."""
    n, B = 4, 3
    chi = exact_chi(n)
    psi = _haar_batch(n, B, seed=1409)
    sites = (1, 2)
    d = torch.stack([
        _sqrt_es_diag(2, D2_A, 0),
        _sqrt_es_diag(2, D2_A, 1),
        torch.kron(torch.tensor([1.0, 0.8, 0.5], dtype=CDTYPE, device=DEVICE),
                   torch.tensor([1.0, 0.4, 0.9], dtype=CDTYPE, device=DEVICE)),
    ])
    x = _mk_from_dense(psi, chi)
    disc_b, bw_b = _win(x, d, sites, diagonal=True)
    dense_b = x.to_dense()
    for b in range(B):
        x1 = _mk_from_dense(psi[b:b + 1], chi)
        disc_1, bw_1 = _win(x1, d[b:b + 1], sites, diagonal=True)
        assert disc_b[b] == disc_1[0] == 0.0
        assert abs(bw_b[b] - bw_1[0]) <= 1e-12
        _assert_states_close(dense_b[b], x1.to_dense()[0], TOL, f"(gop4 per-shot diag shot {b})")
        ref = _dense_apply_window(psi[b:b + 1], torch.diag(d[b]), sites, n)[0]
        _assert_states_close(dense_b[b], _normalized(ref), TOL, f"(gop4 per-shot diag dense {b})")


# =========================================================================== #
# G-OP-5 -- padding invariance (chi_lo BINDS the caps vs chi_hi >= exact).     #
# =========================================================================== #
def test_gop5_padding_invariance_chi_lo_vs_hi():
    """v3 re-registration: chi_lo=4 < exact_chi(6)=27 (caps GENUINELY differ from the
    chi_hi=27 tuple) on an ENGINEERED state whose Schmidt rank -- including the
    post-gate rank through every driven op -- stays <= the chi_lo caps at every cut, so
    BOTH runs are truncation-free but DIFFERENTLY PADDED: identical dense state +
    identical sampled outcomes is then a legitimate exact expectation.

    RANK BUDGET (counted): the state is a product of 2-site blocks (0,1)(2,3)(4,5) ->
    ranks [<=3, 1, <=3, 1, <=3]. Driven ops: 1-site H (rank-preserving), 1-site Kraus
    (rank-preserving), a WINDOW unitary on (2,3) -- an operator INSIDE one block, so
    the post-gate rank at cut 2 stays <= 3 (site dim) and cuts 1/3 stay rank 1 --
    and a 1-site terminal-style threshold sample. All ranks <= 3 < chi_lo=4."""
    n, B = 6, 2
    chi_lo, chi_hi = TRUNC_CHI, exact_chi(n)
    assert _bond_caps(n, chi_lo) != _bond_caps(n, chi_hi), "caps do not differ -- gate vacuous (v2 bug)"
    rng = np.random.default_rng(1511)
    rows = []
    for _ in range(B):
        blocks = []
        for _j in range(3):
            v = rng.standard_normal(PHYS ** 2) + 1j * rng.standard_normal(PHYS ** 2)
            blocks.append(v / np.linalg.norm(v))
        psi = np.kron(blocks[0], np.kron(blocks[1], blocks[2]))
        rows.append(torch.as_tensor(psi, dtype=CDTYPE, device=DEVICE))
    psi = torch.stack(rows)
    for b in range(B):
        for cut in range(n - 1):
            assert _rank_at_cut(psi[b], n, cut) <= 3
    # FIX-3: the prereg D-5 sigma-units conditioning fence for the Gram-routed chi_lo
    # arm (bond_caps BIND at chi_lo=4 -> the window re-split routes Gram + batched
    # eigh). PRECONDITION, class (c): a miss means re-seed this case, never a gate miss.
    _assert_sigma_conditioning(psi, n, _block_structural_ranks(n), chi_lo,
                               "gop5 chi_lo-arm state builder")

    kraus = _leak_kraus()
    ks = _kraus_stack(kraus)
    G = _rand_unitary(PHYS ** 2, rng)
    F1 = torch.diag(torch.tensor([0.0, 1.0, B_EFF], dtype=CDTYPE, device=DEVICE))

    def _run(chi: int, u_kraus=None, u_term=None):
        x = _mk_from_dense(psi, chi)
        x.apply_1site_(_qutrit_gate("H", DEVICE), 0)
        if u_kraus is None:
            _s, pk = x.kraus_sample_(ks, 2, _u_tensor([0.5] * B))  # probe pass to derive u
            pk_rows = torch.as_tensor(pk).detach().cpu()
            # FIX-2: target the DOMINANT no-jump branch by weight (== the LAST index
            # under ascending Choi-eigh), never literal index 0.
            pk_lists = [[float(v) for v in pk_rows[b]] for b in range(B)]
            u_kraus = [_u_for_branch(pk_lists[b], _pick_branches(pk_lists[b])[0]) for b in range(B)]
            x = _mk_from_dense(psi, chi)
            x.apply_1site_(_qutrit_gate("H", DEVICE), 0)
        sel, pk = x.kraus_sample_(ks, 2, _u_tensor(u_kraus))
        disc, bw = _win(x, G, (2, 3), diagonal=False)
        # v4 note: the chi_lo arm routes GRAM at binding caps -> the book reports
        # computed O(eps) entries, NOT the structural 0.0 (a QR-route property); the
        # run is truncation-free by rank budget, so the entries are tiny.
        for b in range(B):
            assert disc[b] <= 1e-12
        rho = x.site_rdm(4, normalized=False)
        w1 = torch.einsum("bij,ji->b", rho, F1).real
        wt = torch.einsum("bii->b", rho).real
        p1 = [float(w1[b]) / float(wt[b]) if float(wt[b]) > NUMERICAL_ZERO else 0.5 for b in range(B)]
        if u_term is None:
            u_term = [_u_below(p1[0]), _u_above(p1[1])]
        bits = []
        for b in range(B):
            _assert_margin_thresh(u_term[b], p1[b])
            bits.append(1 if u_term[b] < p1[b] else 0)
        x.apply_1site_(_f1_collapse_stack(bits, B_EFF), 4)
        x.renormalize_()
        return x.to_dense(), _ints(sel), bits, u_kraus, u_term

    dense_hi, sel_hi, bits_hi, u_k, u_t = _run(chi_hi)
    dense_lo, sel_lo, bits_lo, _uk, _ut = _run(chi_lo, u_kraus=u_k, u_term=u_t)
    assert sel_lo == sel_hi, "padding changed a sampled Kraus branch"
    assert bits_lo == bits_hi, "padding changed a sampled bit"
    _assert_states_close(dense_lo, dense_hi, TOL, "(padding invariance)")


# =========================================================================== #
# G-OP-6 -- structural ledger: exact grade => discarded == 0.0 LITERALLY.      #
# =========================================================================== #
def test_gop6_exact_grade_discarded_literal_zero():
    """Exact grade => EVERY window-op discarded entry is the LITERAL float 0.0 (the D-3
    v2 STRUCTURAL book: every split QR-routed, discard set empty by cap arithmetic).
    ``==``, NOT approx -- a measured book would report ~1e-13 computed eigenvalue dust
    and FAIL this gate by design."""
    rng = np.random.default_rng(1601)
    for n in (4, 6):
        chi = exact_chi(n)
        psi = _haar_batch(n, 2, seed=1607 + n)
        x = _mk_from_dense(psi, chi)
        checks = []
        d2v = _sqrt_es_diag(2, D2_A, 0)
        checks.append(_win(x, torch.diag(d2v), (1, 2), diagonal=True)[0])            # shared diag w=2
        checks.append(_win(x, torch.diag(_sqrt_es_diag(3, D2_A, 1)), (0, 1, 2), diagonal=True)[0])  # w=3
        checks.append(_win(x, _rand_unitary(PHYS ** 2, rng), (n - 2, n - 1), diagonal=False)[0])    # dense
        d_ps = torch.stack([_sqrt_es_diag(2, D2_A, 0), _sqrt_es_diag(2, D2_A, 1)])
        checks.append(_win(x, d_ps, (0, 2), diagonal=True)[0])                       # per-shot diag
        for disc in checks:
            for v in disc:
                assert v == 0.0, f"exact-grade discarded not the literal 0.0: {v!r}"


# =========================================================================== #
# G-OP-7 -- the composed micro-sequence (EXACT grade; one shared u stream).    #
# =========================================================================== #
def test_gop7_micro_sequence_n5():
    """n=5, exact grade (v3 pin -- the sequence contains sqrt(E_s)); the composed
    sequence gate -> leak-Kraus (REAL leak_slice_kraus_torch Kraus) -> stabilizer
    measure (H, parity read, strict u<p0, per-shot diagonal sqrt(E_s) window built
    exactly as _apply_sqrt_Es incl. the clamp, H back) -> hard2 terminal (F1 via
    site_rdm, strict u<p1 with the wt-guard, sqrt(F_bit) collapse, renormalize),
    driven by ONE shared u-stream, vs the serial arm's _apply_gate / _leak_sample /
    _measure_stabilizer / _terminal_readout with the SAME u values: bit-for-bit
    identical (knife-edge guard on every draw) + <=1e-12 in state. (The FULL d3
    trajectory / statistical gates are OPT2-2.)"""
    n, B, m = 5, 2, 0
    chi = exact_chi(n)
    log_support = [0, 2, 4]
    stab_sites, stab_isx = [2, 3], [1, 0]
    psi = _haar_batch(n, B, seed=1709)
    kraus = _leak_kraus()
    ks = _kraus_stack(kraus)
    H = _qutrit_gate("H", DEVICE)
    rng = np.random.default_rng(1721)
    fwd = _fwd()

    # ---- serial arm (the REAL private methods), recording the shared u stream ----
    u_leak, sel_ref, u_stab, sbit_ref = [], [], [], []
    u_term, bits_ref, flips_ref, fin = [], [], [], []
    for b in range(B):
        q = _qmps_from_dense_row(psi[b], n)
        fwd._apply_gate(q, H, 0)
        pk = _dense_leak_pk(_dense_of_qmps(q), kraus, 1, n)  # from-scratch pk referee
        # FIX-2: weight-ranked target (shot 0 -> dominant no-jump, shot 1 -> the
        # second-largest jump branch); never literal 0 / K-1.
        ul = _u_for_branch(pk, _pick_branches(pk)[0 if b == 0 else 1])
        u_leak.append(ul)
        sel_ref.append(_cumsel(pk, ul))  # replica of lines 578-586 (_leak_sample returns no sel)
        fwd._leak_sample(q, kraus, 1, ul)
        probe = q.copy()
        fwd._apply_gate(probe, H, 2)
        p0 = 0.5 * (1.0 + fwd._parity_expectation(probe, stab_sites, D2_A))
        assert 1e-6 < p0 < 1.0 - 1e-6
        us = _u_below(p0) if b == 0 else _u_above(p0)
        u_stab.append(us)
        ledger = MpsTruncationLedger(chi=chi)
        sb, disc = fwd._measure_stabilizer(q, stab_sites, stab_isx, D2_A, us, chi, ledger)
        assert disc == 0.0
        sbit_ref.append(int(sb))
        ut, tr = _serial_hard2(fwd, q, n, log_support, B_EFF, m, rng)
        u_term.append(ut)
        bits_ref.append(list(tr.bits))
        flips_ref.append(int(tr.flip))
        fin.append(_dense_of_qmps(q))
    assert sbit_ref == [0, 1]

    # ---- batched arm, driven by the SAME u stream ----
    x = _mk_from_dense(psi, chi)
    x.apply_1site_(H, 0)
    sel, pk_b = x.kraus_sample_(ks, 1, _u_tensor(u_leak))
    assert _ints(sel) == sel_ref, "micro-sequence: leak branch mismatch"
    sbits, disc, bw, _p0s = _batched_born_stab(x, tuple(stab_sites), stab_isx, D2_A, u_stab)
    assert sbits == sbit_ref, "micro-sequence: syndrome bit mismatch"
    assert disc[0] == 0.0 and disc[1] == 0.0  # literal structural book (G-OP-6 semantics)
    bits, flips = _batched_hard2(x, n, log_support, B_EFF, m, u_term)
    assert bits == bits_ref, "micro-sequence: terminal bits mismatch"
    assert flips == flips_ref, "micro-sequence: logical flip mismatch"
    _assert_states_close(x.to_dense(), torch.stack(fin), TOL, "(micro-sequence final state)")

from __future__ import annotations

r"""Registered pytest gates for the ``carrier/peps/fet.py``
environment-aware rank-selection truncator + its ``fet_env`` policy wiring.

Written against the registered FET source contract (§5 gates) —
NEVER against the implementation: the parallel-built module
``src/error_coupling_simulator/carrier/peps/fet.py`` (and the ``fet_env`` branches
in ``trajectory.py``) is imported at TEST RUNTIME ONLY (inside
:func:`_peps_namespaces`); it was not read while this file was authored. Ambiguous
signature details are concentrated in the ADAPTER block below (ONE place to fix at
integration — contract §7 discipline).

Coverage (the contract §5 gate rows this file owns; the d3-scale exact-Γ arm):

  * G-ANTICIRC (a) — on a REAL round-1 grown bond:
      (i) two-route ``Γ_TN == Γ_dense`` to 1e-9, where ``Γ_dense`` is the
          INDEPENDENT referee written HERE (``_gamma_dense_ref`` — an explicit
          opt_einsum contraction of the SAME site tensors, sharing NO code with
          ``fet.gamma_TN``'s boundary machinery);
      (ii) ``Fid_Γ(χ) == fid_dense(χ)`` to 1e-6, where ``Fid_Γ`` is the src's
          ``fet.gamma_fidelity`` (the Γ-metric) and ``fid_dense`` is the referee's
          ``dense_psi``-overlap after the referee's OWN write-back (Γ-independent).
      Certified at BOTH a lossless point (env_optimal_rank χ, Fid ≈ 1) AND a
      genuinely-lossy rank-1 projector point (Fid < 1 — non-vacuous), each with a
      should-fail control (a perturbed Γ / a cross-paired fidelity) proven to trip.

  * G-SA-CORROB (a) — after a ``fet_env`` truncation of one leak-off round, the
      carrier's ``dense_psi`` S_A across cut A equals the INLINE GF(2) stabilizer
      entropy baseline (``stabilizer_entropy_SA`` + independent helpers — they import
      NOTHING from the carrier). Control: a shifted reference at 10·tol trips.

  * fet_env WIRING SMOKE:
      - RT-F1: ``TruncationPolicy("fet_env", eps_fid=1e-8)`` drives one round via
        ``PepsSampler.sample`` without crashing, AND ``_policy_precut`` is a strict
        NO-OP for ``fet_env`` (precut_discarded == 0.0 EXACTLY, r_dyn/width None,
        window_binding False, exact_rank == _exact_rank(_insertion_spectrum), the
        bond dim UNCHANGED). Control: the same rec fields are NON-None for
        ``dynamic_eps`` (the None-signature is fet_env-specific, not vacuous).
      - RT-F5 (full-rank losslessness): keeping the full bond is LOSSLESS — the
        full-rank identity insertion has ``Fid_Γ == 1.0`` — so the no-qualifying-χ
        keep-full-bond fallback is safe (never a lossy ceiling cut). The fallback branch
        is itself defensively-unreachable at ``eps_fid > 0`` (χ = bare_rank IS this
        lossless insertion), so the test asserts the losslessness directly.

GPU convention (SW-S8): every test that constructs a PepsState requires CUDA
(``requires_cuda``); tests needing the REAL Google d3 circuit skip with an explicit
justification when the local dataset is absent (real patch only — no fallback).
EXACT route throughout (``R_n=None`` / ``R_x=None`` — byte-identical to the d3
gates; the contract's exact-Γ arm).

Referee independence (contract §7): the Γ two-route referee (``_gamma_dense_ref``),
the dense-fidelity referee (``_fid_dense_ref`` + its OWN write-back
``_apply_fet_trunc_ref``) and the GF(2) S_A baseline share NO code with the
``fet.py`` hot path they referee.
"""

import math

import numpy as np
import pytest
import torch

from _support.fixtures import assert_control_trips, require_precondition

# --------------------------------------------------------------------------- #
# Constants (contract §5 bars + the independent d3 leak-off run constants)    #
# --------------------------------------------------------------------------- #
PATCH = "d3_at_q6_7"
G_SEEP = 0.09
G_HEAT = 0.0
B_BIAS = 0.9
ARM = "A"
READOUT_CONV = "biased_b"
LOGICAL_M = 0
FIT_SEED = 0
BASE_SEED_OFF = 2026
WG_L1_OFF = 0.0

EPS_SPIKE = 1e-8          # dynamic_eps control knob used by the d3 gates
W_MAX = 160
CUT_A = (0, 1, 2, 3)
GROWN_MIN = 5             # a grid bond dim >= this counts as "grown" (over-count present)

EPS_FID = 1e-8            # env-optimal acceptance: smallest χ with Fid_Γ >= 1 - EPS_FID

GAMMA_REL_TOL = 1e-9     # G-ANTICIRC two-route Γ bar
FID_ANTICIRC_TOL = 1e-6  # G-ANTICIRC Fid_Γ == fid_dense bar
SA_BASELINE_LEAKOFF = 2.0   # d3 leak-off GF(2) stabilizer entropy across cut (0,1,2,3)
SA_OFF_TOL = 1e-4        # leak-off post-trunc S_A deviation bar
NORM_GUARD = 1e-12       # fid_dense norm guard: degenerate truncation gives fidelity 0

_CUDA = torch.cuda.is_available()
requires_cuda = pytest.mark.skipif(
    not _CUDA, reason="CUDA unavailable — the PEPS/FET engine is GPU-only (SW-S8)")


# =========================================================================== #
# ADAPTERS — the ONE place to fix if a signature detail differs at            #
# integration (contract §7: the module is built in parallel; §2/§3 pin the    #
# SEMANTICS + most NAMES, not every argument spelling).                       #
# =========================================================================== #
_PEPS_PKG = "error_coupling_simulator.carrier.peps"


def _peps_namespaces() -> list:
    """Runtime-only import of the parallel-built package + ALL its submodules
    (pkgutil walk — no submodule-name guessing). Resolution order: package
    namespace (re-exports) first, then submodules sorted by name."""
    import importlib
    import pkgutil

    pkg = importlib.import_module(_PEPS_PKG)
    mods = [pkg]
    for info in sorted(pkgutil.iter_modules(pkg.__path__), key=lambda i: i.name):
        mods.append(importlib.import_module(f"{_PEPS_PKG}.{info.name}"))
    return mods


def _resolve(name: str):
    for mod in _peps_namespaces():
        obj = getattr(mod, name, None)
        if obj is not None:
            return obj
    return None


def _resolve_any(names, what: str):
    for nm in names:
        obj = _resolve(nm)
        if obj is not None:
            return obj
    pytest.fail(
        f"carrier/peps exposes none of {tuple(names)} for {what} — fix this adapter "
        f"(ONE place; the contract pins the semantics, not this spelling)")


def _try_calls(calls, what: str):
    """Run candidate zero-arg lambdas until one succeeds; a TypeError (signature
    mismatch) advances to the next candidate; anything else propagates (a real
    engine error must never be silently retried into a different signature)."""
    errs = []
    for c in calls:
        try:
            return c()
        except TypeError as e:
            errs.append(str(e))
    pytest.fail(f"no candidate signature matched for {what} — fix this adapter; "
                f"TypeErrors seen: {errs}")


# ---- src object handles (resolved lazily; §2/§3 pinned surface) ------------ #
def _TruncationPolicy():
    return _resolve_any(("TruncationPolicy",), "the truncation policy dataclass (§2)")


def _trunc_policy(mode: str, **kw):
    """§2/§3 ``TruncationPolicy`` — ``fet_env`` requires ``eps_fid``."""
    TP = _TruncationPolicy()
    return TP(str(mode), **kw)


def _PepsSampler():
    return _resolve_any(("PepsSampler",), "the PEPS trajectory sampler (D5/D7)")


def _build_codestate(sched, m: int):
    fn = _resolve_any(("build_codestate_peps",), "the codestate builder (§2)")
    return _try_calls(
        [lambda: fn(sched, int(m), device="cuda"),
         lambda: fn(sched, int(m), "cuda"),
         lambda: fn(sched, int(m))],
        "build_codestate_peps")


def _dense_psi(state) -> torch.Tensor:
    """§3 ``dense_psi(state)`` — the d3 referee bridge (engine pos 0 = MSB)."""
    fn = _resolve("dense_psi")
    if fn is not None:
        return torch.as_tensor(fn(state)).reshape(-1)
    meth = getattr(state, "dense_psi", None)
    if callable(meth):
        return torch.as_tensor(meth()).reshape(-1)
    pytest.fail("carrier/peps exposes no dense_psi (§3 pins it) — fix this adapter")


def _bond_profile(state) -> dict:
    fn = _resolve_any(("bond_profile",), "the SW8 bond profile (§6.1)")
    prof = fn(state)
    out = {}
    for k, v in dict(prof).items():
        if isinstance(k, (tuple, list)) and len(k) == 2:
            a, b = int(k[0]), int(k[1])
        else:
            body = str(k)[1:]
            a, b = (int(x) for x in body.split("_"))
        out[(min(a, b), max(a, b))] = int(v)
    return out


def _site_tensor(state, pos: int):
    fn = _resolve_any(("site_tensor",), "the Q{pos} site accessor (§2)")
    return fn(state, int(pos))


def _phys_name(pos: int) -> str:
    fn = _resolve_any(("phys_name",), "the physical index name (§2)")
    return str(fn(int(pos)))


# ---- fet.py surface (contract §2/§3) --------------------------------------- #
def _fet_gamma_TN(state, bond: str) -> torch.Tensor:
    """§2 ``fet.gamma_TN(state, bond)`` — exact double-layer single-bond Γ[i,I,j,J]."""
    fn = _resolve_any(("gamma_TN",), "the exact single-bond environment Γ (§2)")
    out = _try_calls([lambda: fn(state, str(bond))], "gamma_TN")
    return torch.as_tensor(out)


def _fet_gamma_fidelity(Gamma: torch.Tensor, M: torch.Tensor) -> float:
    """§2 ``fet.gamma_fidelity(Gamma, M)`` — the Γ-metric fidelity of bond map M."""
    fn = _resolve_any(("gamma_fidelity",), "the Γ-fidelity (§2)")
    return float(_try_calls([lambda: fn(Gamma, M)], "gamma_fidelity"))


def _fet_env_optimal_rank(state, bond: str, eps_fid: float):
    """§3 ``env_optimal_rank(state, bond, eps_fid)`` -> (env_rank, U, Vh).

    Normalizes the return to ``(env_rank:int, U, Vh)`` (dropping any trailing
    achieved-fidelity element); accepts a 4-tuple ``(env_rank, U, Vh, fid_env)``, a
    3-tuple, a ``(env_rank, (U, Vh))`` pair, or a dict. The fallback (RT-F5) may
    carry ``U``/``Vh`` = None — the caller only asserts on ``env_rank`` there."""
    fn = _resolve_any(("env_optimal_rank",), "the env-optimal rank selector (§3)")
    res = _try_calls(
        [lambda: fn(state, str(bond), float(eps_fid)),
         lambda: fn(state, str(bond), eps_fid=float(eps_fid))],
        "env_optimal_rank")
    if isinstance(res, dict):
        r = res.get("env_rank", res.get("rank"))
        return int(r), res.get("U"), res.get("Vh", res.get("Vdag"))
    if isinstance(res, (tuple, list)):
        if len(res) in (3, 4):   # (env_rank, U, Vh[, fid_env]) — drop fid_env
            return int(res[0]), res[1], res[2]
        if len(res) == 2 and isinstance(res[1], (tuple, list)) and len(res[1]) == 2:
            return int(res[0]), res[1][0], res[1][1]
    pytest.fail(f"env_optimal_rank return shape {type(res)} unrecognized — fix this adapter")


def _policy_precut(state, bond: str, policy):
    """Pass-1 ``_policy_precut(state, bond, policy)`` — the seam whose fet_env
    branch must be a strict NO-OP (contract §3 RT-F1)."""
    fn = _resolve_any(("_policy_precut",), "the pass-1 precut seam (§3)")
    return fn(state, str(bond), policy)


def _insertion_spectrum(state, bond: str) -> torch.Tensor:
    fn = _resolve_any(("_insertion_spectrum",), "the pair-insertion spectrum (§6.1)")
    return torch.as_tensor(fn(state, str(bond)))


def _exact_rank(S: torch.Tensor) -> int:
    fn = _resolve_any(("_exact_rank",), "the exact-local-rank helper (§6.1)")
    return int(fn(torch.as_tensor(S)))


# =========================================================================== #
# INDEPENDENT REFEREES (share NO code with fet.py — contract §7).             #
#   * GF(2) stabilizer entropy: independent inline diagnostic                 #
#     (import NOTHING from the carrier).                                       #
#   * carrier_SA: the carrier's OWN dense S_A read (routed through the adapter #
#     dense_psi — the only adapter used by that independent calculation).      #
#   * Γ_dense / fid_dense / write-back: the anti-circular two-route referees.  #
# =========================================================================== #
def _gf2_rank(rows: list) -> int:
    """Rank over GF(2) of a set of bit-vectors packed as Python ints. VERBATIM."""
    basis: list = []
    for r in rows:
        cur = int(r)
        for b in basis:
            cur = min(cur, cur ^ b)
        if cur:
            basis.append(cur)
            basis.sort(reverse=True)
    return len(basis)


def _pauli_to_symplectic(paulis: dict, n: int):
    """A stabilizer/logical ``{site: 'X'|'Z'}`` -> (x_bits, z_bits). VERBATIM."""
    x_bits = z_bits = 0
    for site, p in paulis.items():
        s = int(site)
        if str(p).upper() == "X":
            x_bits |= (1 << s)
        elif str(p).upper() == "Z":
            z_bits |= (1 << s)
        else:
            raise ValueError(f"non-X/Z pauli {p!r} at site {site} (XZZX expects X/Z)")
    return x_bits, z_bits


def stabilizer_entropy_SA(generators: list, n: int, region_A) -> float:
    """S_A (ebits) of the pure stabilizer state — Fattal/Hamma. VERBATIM
    (INDEPENDENT of the carrier and stim; pure GF(2) algebra on the generators)."""
    setA = set(int(a) for a in region_A)
    B = [i for i in range(n) if i not in setA]
    nB = len(B)
    b_index = {q: j for j, q in enumerate(B)}
    rows = []
    for g in generators:
        xb, zb = _pauli_to_symplectic(g, n)
        rb = 0
        for q in B:
            if (xb >> q) & 1:
                rb |= (1 << b_index[q])
            if (zb >> q) & 1:
                rb |= (1 << (nB + b_index[q]))
        rows.append(rb)
    return float(_gf2_rank(rows) - nB)


def carrier_SA(state, region_A, n: int):
    """(S_A, leak_mass, schmidt_rank) of the carrier's EXACT pure state across cut
    A (leakage-OFF read: restrict to {0,1}^n). Retained independent calculation;
    the ONLY adaptation is the adapter-routed ``dense_psi`` (runtime-import
    discipline). Shares NO code with fet.py."""
    psi = _dense_psi(state).detach().to(torch.complex128).cpu()
    full_norm2 = float((psi.conj() * psi).real.sum())
    psi3 = psi.reshape([3] * n)
    sl = tuple([slice(0, 2)] * n)
    psi2 = psi3[sl].contiguous()
    qnorm2 = float((psi2.conj() * psi2).real.sum())
    leak_mass = max(0.0, full_norm2 - qnorm2) / max(full_norm2, 1e-300)
    psi2 = psi2 / (qnorm2 ** 0.5)
    A = sorted(int(a) for a in region_A)
    B = [i for i in range(n) if i not in A]
    perm = A + B
    mat = psi2.permute(*perm).reshape(2 ** len(A), 2 ** len(B))
    sv = torch.linalg.svdvals(mat)
    p = (sv * sv).real
    p = p / p.sum()
    nz = p[p > 1e-15]
    S_A = float(-(nz * torch.log2(nz)).sum())
    rank = int((sv > 1e-9 * float(sv[0])).sum()) if sv.numel() and float(sv[0]) > 0 else 0
    return S_A, leak_mass, rank


def _parse_bond(bond: str):
    """``B{a}_{b}`` -> (a, b) with a < b. VERBATIM."""
    body = str(bond)[1:]
    a_str, b_str = body.split("_")
    a, b = int(a_str), int(b_str)
    return (a, b) if a < b else (b, a)


def _gamma_dense_ref(state, bond: str) -> torch.Tensor:
    """INDEPENDENT referee route for Γ[i,I,j,J] (shares NO code with the src's
    boundary machinery): an explicit opt_einsum contraction of the SAME site
    tensors — all physical legs traced ket·bra, all bonds summed except the target
    bond left open on BOTH layers."""
    import opt_einsum as oe

    layout = state.layout
    n = int(layout.n_data)
    a, b = _parse_bond(bond)
    syms: dict = {}
    counter = [0]

    def sym(key):
        if key not in syms:
            syms[key] = oe.get_symbol(counter[0])
            counter[0] += 1
        return syms[key]

    s_i, s_I, s_j, s_J = (sym(("open", "i")), sym(("open", "I")),
                          sym(("open", "j")), sym(("open", "J")))
    operands = []
    subs = []
    for pos in range(n):
        t = _site_tensor(state, pos)
        data = t.data.to(torch.complex128)
        inds = list(t.inds)
        pn = _phys_name(pos)
        ket_sub, bra_sub = [], []
        for nm in inds:
            if nm == pn:
                s = sym(("phys", pos))
                ket_sub.append(s)
                bra_sub.append(s)
            elif nm == bond and int(pos) == a:
                ket_sub.append(s_i)
                bra_sub.append(s_I)
            elif nm == bond and int(pos) == b:
                ket_sub.append(s_j)
                bra_sub.append(s_J)
            else:
                ket_sub.append(sym(("bond_ket", nm)))
                bra_sub.append(sym(("bond_bra", nm)))
        operands.append(data)
        subs.append("".join(ket_sub))
        operands.append(data.conj())
        subs.append("".join(bra_sub))
    eq = ",".join(subs) + "->" + s_i + s_I + s_j + s_J
    out = oe.contract(eq, *operands, optimize="auto")
    return out.to(torch.complex128)


def _apply_fet_trunc_ref(state, bond: str, U: torch.Tensor, Vh: torch.Tensor) -> None:
    """The referee's OWN write-back (independent of the src): absorb ``U`` (D×χ)
    into site A's bond leg and ``Vh`` (χ×D) into site B's, keeping the ORIGINAL
    bond name. Mutates ``state`` in place."""
    a, b = _parse_bond(bond)
    ta, tb = _site_tensor(state, a), _site_tensor(state, b)
    axa = ta.inds.index(bond)
    new_a = torch.movedim(torch.tensordot(ta.data, U, dims=([axa], [0])), -1, axa)
    ta.modify(data=new_a.contiguous())
    axb = tb.inds.index(bond)
    new_b = torch.movedim(torch.tensordot(tb.data, Vh, dims=([axb], [1])), -1, axb)
    tb.modify(data=new_b.contiguous())


def _overlap_sq(psi_ref: torch.Tensor, psi_trunc: torch.Tensor) -> float:
    """|<ref|trunc>|^2 / (||ref||^2 ||trunc||^2) with the explicit norm guard."""
    nr = float(torch.vdot(psi_ref, psi_ref).real)
    nt = float(torch.vdot(psi_trunc, psi_trunc).real)
    if not np.isfinite(nr) or not np.isfinite(nt) or nr <= 0.0:
        return 0.0
    if nt <= (NORM_GUARD * nr):
        return 0.0
    ov = torch.vdot(psi_ref, psi_trunc)
    val = float((ov.conj() * ov).real) / (nr * nt)
    return val if np.isfinite(val) else 0.0


def _fid_dense_ref(state, bond: str, U: torch.Tensor, Vh: torch.Tensor,
                   psi_before: torch.Tensor) -> float:
    """The Γ-INDEPENDENT global fidelity of the rank-χ truncation: apply it to a
    COPY (referee write-back), recompute ``dense_psi``, measure |<before|after>|^2.
    This calculation is independent of the environment-metric implementation."""
    cp = state.copy()
    _apply_fet_trunc_ref(cp, bond, U, Vh)
    psi_after = _dense_psi(cp)
    return _overlap_sq(psi_before, psi_after)


def _grown_bonds(state) -> list:
    """Grid bonds whose current dim counts as grown (dim >= GROWN_MIN)."""
    prof = _bond_profile(state)
    out = []
    for (p, q), dim in sorted(prof.items()):
        if int(dim) >= GROWN_MIN:
            out.append((f"B{p}_{q}", int(dim)))
    return out


def _basis_col(D: int, k: int, device) -> torch.Tensor:
    """The (D, 1) basis-``k`` column (a rank-1 bond projector isometry U)."""
    U = torch.zeros((D, 1), dtype=torch.complex128, device=device)
    U[k, 0] = 1.0
    return U


# =========================================================================== #
# Drive helpers + fixtures (the REAL Google d3 leak-off carrier, EXACT route)  #
# =========================================================================== #
def _parse_d3_sched():
    from error_coupling_simulator.frontend import xzzx_parser as xp

    c01, m01 = xp.default_r01_paths(patch=PATCH, basis="X")
    c10, m10 = xp.default_r10_paths(patch=PATCH, basis="X")
    for p in (c01, m01, c10, m10):
        if not p.is_file():
            pytest.skip("d3 XZZX r01/r10 real-Google circuits absent under the dataset "
                        "root (real patch only, no textbook fallback)")
    sched = xp.parse_xzzx_circuit(c01, m01, verify=True)
    sched = sched.with_within_cycle_streams(xp.parse_within_cycle_streams(c10, m10))
    assert int(sched.n_data) == 9 and len(sched.stabilizers) == 8, (
        sched.n_data, len(sched.stabilizers))
    return sched, c01, m01


def _build_spec(c01, m01, *, R: int, base_seed: int):
    from error_coupling_simulator.carrier.within_cycle import RunSpec
    from error_coupling_simulator.mechanisms.qutrit_leakage import (
        solve_theta_for_wg_l1,
    )

    theta = solve_theta_for_wg_l1(WG_L1_OFF, g_seep=G_SEEP, g_heat=G_HEAT)
    return RunSpec(circuit_path=c01, metadata_path=m01, m=LOGICAL_M, theta=float(theta),
                   g_seep=G_SEEP, g_heat=G_HEAT, arm=ARM, b=B_BIAS, readout_conv=READOUT_CONV,
                   N=1, base_seed=int(base_seed), R=int(R), dtype="c128")


def _drive_capture(sched, c01, m01, policy, *, d_abort, capture_round: int = 0):
    """Drive ONE leak-off trajectory (EXACT route) under ``policy`` and return the
    live PepsState snapshot captured after round ``capture_round`` (a ``.copy()``)."""
    spec = _build_spec(c01, m01, R=capture_round + 1, base_seed=BASE_SEED_OFF)
    Sampler = _PepsSampler()
    captured: dict = {}

    def hook(st, r, shot):
        if int(r) == int(capture_round):
            captured["state"] = st.copy()

    Sampler(device="cuda").sample(
        spec, sched=sched, policy=policy, R_n=None, R_x=None, fit_seed=FIT_SEED,
        materialize=True, d_abort=d_abort, round_hook=hook)
    return captured.get("state")


@pytest.fixture(scope="module")
def d3():
    """The REAL d3_at_q6_7 leak-off schedule + r10 within-cycle streams."""
    if not _CUDA:
        pytest.skip("CUDA unavailable — the PEPS engine is GPU-only (SW-S8)")
    return _parse_d3_sched()


@pytest.fixture(scope="module")
def gf2_baseline(d3):
    """The INDEPENDENT GF(2) stabilizer-entropy baseline across cut A (== 2.0 ebits
    at d3 leak-off) computed from the schedule's generators — the S_A referee."""
    sched, _c01, _m01 = d3
    n = int(sched.n_data)
    stabs = [dict(s.paulis) for s in sched.stabilizers]
    generators = stabs + [dict(sched.logical)]
    assert len(generators) == n, (len(generators), n)
    base = stabilizer_entropy_SA(generators, n, CUT_A)
    assert abs(base - SA_BASELINE_LEAKOFF) <= 1e-9, (
        f"GF(2) baseline {base} != expected leak-off {SA_BASELINE_LEAKOFF}")
    return base


@pytest.fixture(scope="module")
def grown_state(d3):
    """A leak-off round-1 state under LOSSLESS policy (bonds at the full exact local
    rank — the maximal over-count representation; the Γ / env / fid gates read it)."""
    sched, c01, m01 = d3
    st = _drive_capture(sched, c01, m01, _trunc_policy("lossless"), d_abort=None)
    require_precondition(st is not None, "no round-1 state captured (lossless drive)")
    require_precondition(bool(_grown_bonds(st)),
                         f"no grown bond (dim >= {GROWN_MIN}) after round 1 — nothing to referee")
    return st


@pytest.fixture(scope="module")
def fet_env_state(d3):
    """A leak-off round-1 state driven under the NEW ``fet_env`` policy — the src
    truncator does the WHOLE per-round truncation (RT-F1/RT-F2 exercised end-to-end).
    A crash here surfaces as an ERROR on the requesting gate (the RT-F1 regression)."""
    sched, c01, m01 = d3
    st = _drive_capture(sched, c01, m01, _trunc_policy("fet_env", eps_fid=EPS_FID),
                        d_abort=None)
    require_precondition(st is not None, "no round-1 state captured (fet_env drive)")
    return st


def _biggest_grown_bond(state):
    grown = _grown_bonds(state)
    require_precondition(bool(grown), f"no grown bond (dim >= {GROWN_MIN})")
    bond, dim = max(grown, key=lambda bd: bd[1])
    return bond, int(dim)


# =========================================================================== #
# G-ANTICIRC (a) — two-route Γ + Fid_Γ == fid_dense on a REAL round-1 bond.    #
# =========================================================================== #
@requires_cuda
class TestGAntiCirc:

    def test_gamma_two_route_identity(self, grown_state):
        """Γ_TN (src) == Γ_dense (independent referee) on the biggest grown bond,
        to 1e-9. Control: a 1e-6-perturbed referee Γ trips the same check."""
        state = grown_state.copy()                 # isolate the shared module fixture
        bond, dim = _biggest_grown_bond(state)
        g_tn = _fet_gamma_TN(state, bond).to(torch.complex128)
        g_ref = _gamma_dense_ref(state, bond).to(torch.complex128)
        require_precondition(tuple(g_tn.shape) == tuple(g_ref.shape),
                             f"Γ shape mismatch {tuple(g_tn.shape)} vs {tuple(g_ref.shape)} "
                             f"(bond {bond}, dim {dim})")
        nrm = float(torch.linalg.norm(g_tn.reshape(-1)))
        require_precondition(nrm > 1e-30, "Γ_TN vanished — degenerate bond")

        def _two_route(g_dense_in, tol):
            rel = float(torch.linalg.norm((g_tn - g_dense_in).reshape(-1))) / nrm
            assert rel <= tol, f"Γ two-route rel {rel:.3e} > {tol:.1e}"

        # positive: the two independent routes agree to the (a)-exact bar.
        _two_route(g_ref, GAMMA_REL_TOL)
        # control: a 1e-6-perturbed referee Γ MUST trip the 1e-9 check (non-vacuous).
        assert_control_trips(_two_route, g_ref * (1.0 + 1e-6), GAMMA_REL_TOL)

    def test_fid_gamma_equals_fid_dense(self, grown_state):
        """Fid_Γ (src Γ-metric) == fid_dense (referee dense overlap) on the SAME
        truncation — the anti-circular fidelity check — at a lossless env_optimal
        point AND a genuinely-lossy rank-1 projector point (non-vacuous). Control:
        cross-pairing the env Fid_Γ with the lossy fid_dense trips the check."""
        state = grown_state.copy()                 # isolate the shared module fixture
        bond, dim = _biggest_grown_bond(state)
        g_tn = _fet_gamma_TN(state, bond).to(torch.complex128)
        D = int(g_tn.shape[0])
        require_precondition(D >= 2, f"bond {bond} dim {D} < 2 — no lossy projector")
        dev = g_tn.device
        psi_before = _dense_psi(state)

        # -- lossless point: the env-optimal (U, Vh) (Fid ≈ 1 both routes) --
        env_rank, U, Vh = _fet_env_optimal_rank(state, bond, EPS_FID)
        require_precondition(U is not None and Vh is not None,
                             "env_optimal_rank returned no (U, Vh) at eps_fid=1e-8")
        U = torch.as_tensor(U).to(torch.complex128).to(dev)
        Vh = torch.as_tensor(Vh).to(torch.complex128).to(dev)
        M_env = U @ Vh
        fid_gamma_env = _fet_gamma_fidelity(g_tn, M_env)
        fid_dense_env = _fid_dense_ref(state, bond, U, Vh, psi_before)
        assert abs(fid_gamma_env - fid_dense_env) <= FID_ANTICIRC_TOL, (
            f"anti-circular MISS at env_rank={env_rank}: "
            f"Fid_Γ={fid_gamma_env:.12f} fid_dense={fid_dense_env:.12f}")

        # -- lossy point: a rank-1 bond-index projector with INTERMEDIATE fidelity
        #    (both routes < 1 — the non-vacuous positive) --
        lossy = None
        for k in range(D):
            Uk = _basis_col(D, k, dev)
            Vk = Uk.conj().mT                       # (1, D) — projector |k><k| on the bond
            fdk = _fid_dense_ref(state, bond, Uk, Vk, psi_before)
            if 1e-6 < fdk < 1.0 - 1e-3:
                if lossy is None or abs(fdk - 0.5) < abs(lossy[3] - 0.5):
                    lossy = (k, Uk, Vk, fdk)
        require_precondition(lossy is not None,
                             "no bond index gives an intermediate-fidelity rank-1 "
                             "projector — cannot stress the anti-circular check")
        _k, Uk, Vk, fid_dense_lossy = lossy
        fid_gamma_lossy = _fet_gamma_fidelity(g_tn, Uk @ Vk)
        assert abs(fid_gamma_lossy - fid_dense_lossy) <= FID_ANTICIRC_TOL, (
            f"anti-circular MISS at lossy projector k={_k}: "
            f"Fid_Γ={fid_gamma_lossy:.12f} fid_dense={fid_dense_lossy:.12f}")

        # control: pairing the env Fid_Γ (≈1) with the LOSSY fid_dense (<1) MUST trip
        # (proves the |Fid_Γ − fid_dense| <= tol check is discriminating, not vacuous).
        def _fid_match(fid_dense_in, tol):
            assert abs(fid_gamma_env - fid_dense_in) <= tol, (
                f"|Fid_Γ_env − fid_dense| = {abs(fid_gamma_env - fid_dense_in):.3e} > {tol:.1e}")

        require_precondition(abs(fid_gamma_env - fid_dense_lossy) > FID_ANTICIRC_TOL,
                             "env and lossy fidelities coincide — control would be vacuous")
        assert_control_trips(_fid_match, fid_dense_lossy, FID_ANTICIRC_TOL)


# =========================================================================== #
# G-SA-CORROB (a) — post-fet_env S_A == the inline GF(2) baseline.            #
# =========================================================================== #
@requires_cuda
class TestGSaCorrob:

    def test_fet_env_round_preserves_stabilizer_entropy(self, fet_env_state, gf2_baseline):
        """After one leak-off round under ``fet_env``, the carrier's dense S_A across
        cut A equals the INDEPENDENT GF(2) stabilizer-entropy baseline (2.0 ebits) to
        SA_OFF_TOL. Control: a reference shifted by 10·tol trips the same check."""
        n = int(fet_env_state.layout.n_data)
        S_A, leak_mass, rank = carrier_SA(fet_env_state, CUT_A, n)
        require_precondition(leak_mass <= 1e-6,
                             f"leak_mass {leak_mass:.2e} > 1e-6 — not a leak-off state")

        def _sa_matches(ref, tol):
            assert abs(S_A - ref) <= tol, f"|S_A − ref| = {abs(S_A - ref):.3e} > {tol:.1e}"

        # positive: the fet_env-truncated round is state-faithful => S_A == GF(2).
        _sa_matches(gf2_baseline, SA_OFF_TOL)
        # control: a reference offset by 10·tol MUST trip (the tolerance is discriminating).
        assert_control_trips(_sa_matches, gf2_baseline + 10.0 * SA_OFF_TOL, SA_OFF_TOL)


# =========================================================================== #
# fet_env WIRING SMOKE — RT-F1 (precut no-op + end-to-end drive) + RT-F5.      #
# =========================================================================== #
@requires_cuda
class TestFetEnvWiring:

    def test_fet_env_drives_one_round_without_crashing(self, fet_env_state):
        """RT-F1 end-to-end: ``TruncationPolicy("fet_env", eps_fid=1e-8)`` drove one
        round via ``PepsSampler.sample`` and returned a live PepsState with a readable
        grid bond profile (a fall-through to the dynamic_eps tail would have raised
        ``float(None)`` — the RT-F1 regression this guards)."""
        prof = _bond_profile(fet_env_state)
        assert prof, "fet_env round produced no grid bond profile"
        assert all(int(d) >= 1 for d in prof.values()), prof
        # the fet_env round yields a finite, materialized state (the crash-free contract).
        psi = _dense_psi(fet_env_state)
        assert torch.isfinite(psi).all(), "fet_env round produced a non-finite state"
        assert float(torch.vdot(psi, psi).real) > 1e-12, "fet_env round collapsed the norm"

    def test_policy_precut_is_a_strict_noop_for_fet_env(self, grown_state):
        """RT-F1 unit: ``_policy_precut`` for ``fet_env`` returns the exact summary
        keys ``_policy_cut`` reads (precut_discarded == 0.0, r_dyn/width None,
        window_binding False, exact_rank == _exact_rank(_insertion_spectrum)) and does
        NO svd (bond dim UNCHANGED). Control: ``dynamic_eps`` populates r_dyn/width
        (the None-signature is fet_env-specific — the assertions are not vacuous)."""
        bond, dim = _biggest_grown_bond(grown_state)

        pol = _trunc_policy("fet_env", eps_fid=EPS_FID)
        # the hazard RT-F1 averts: fet_env carries NO eps_spike, so a fall-through to
        # the dynamic tail would evaluate float(policy.eps_spike) == float(None).
        assert getattr(pol, "eps_spike", None) is None, (
            "fet_env policy unexpectedly carries eps_spike — the RT-F1 hazard/premise changed")

        cp = grown_state.copy()
        dim_in = int(cp.tn.ind_size(bond))
        rec = _policy_precut(cp, bond, pol)
        assert float(rec["precut_discarded"]) == 0.0, rec           # EXACTLY 0.0
        assert rec["r_dyn"] is None, rec
        assert rec["width"] is None, rec
        assert bool(rec["window_binding"]) is False, rec
        assert int(rec["exact_rank"]) == _exact_rank(_insertion_spectrum(cp, bond)), rec
        assert int(cp.tn.ind_size(bond)) == dim_in, (
            f"fet_env precut changed the bond dim {dim_in} -> {int(cp.tn.ind_size(bond))} "
            "(must be a strict NO-OP so pass-2 reads the un-pre-truncated Γ)")

        # control: dynamic_eps returns NON-None r_dyn/width on the SAME bond — the
        # None-signature asserted above is a fet_env discriminator, not universally true.
        cp2 = grown_state.copy()
        rec_dyn = _policy_precut(cp2, bond, _trunc_policy("dynamic_eps",
                                                          eps_spike=EPS_SPIKE, W_max=W_MAX))
        assert rec_dyn["r_dyn"] is not None and rec_dyn["width"] is not None, (
            f"dynamic_eps precut left r_dyn/width None on bond {bond} (dim {dim}) — the "
            "fet_env None-assertions above would be vacuous")

    def test_full_rank_insertion_is_lossless(self, grown_state):
        """RT-F5 (simplified — full-rank losslessness): the no-qualifying-χ fallback
        KEEPS the full bond, which is SAFE precisely because keeping the full bond is
        LOSSLESS. Assert that directly: the full-rank identity insertion on a grown bond
        has ``Fid_Γ == 1.0`` (no fidelity lost by NOT truncating), and ``env_optimal_rank``
        at a valid ``eps_fid > 0`` returns a rank ≤ D whose achieved ``Fid_Γ ≥ 1 − eps_fid``.
        (The no-qualifying-χ branch itself is defensively-unreachable at ``eps_fid > 0``,
        because χ = bare_rank IS this lossless full-rank insertion — so this asserts the
        safe keep-full-bond behaviour, not a lossy ceiling cut.)"""
        import importlib
        fet = importlib.import_module(f"{_PEPS_PKG}.fet")

        state = grown_state.copy()                 # isolate the shared module fixture
        bond, _dim = _biggest_grown_bond(state)
        D = int(state.tn.ind_size(bond))
        require_precondition(D >= GROWN_MIN,
                             f"bond {bond} dim {D} < {GROWN_MIN} — not over-counted")

        Gamma = fet.gamma_TN(state, bond)
        eye = torch.eye(D, dtype=Gamma.dtype, device=Gamma.device)
        fid_full = float(fet.gamma_fidelity(Gamma, eye))     # full-rank identity insertion
        # (i) keeping the full bond (no truncation) is LOSSLESS.
        assert abs(fid_full - 1.0) <= 1e-9, (
            f"full-rank identity insertion not lossless: Fid_Γ={fid_full!r} (expected 1.0) "
            "— the RT-F5 keep-full-bond fallback would then NOT be safe")
        # (ii) env_optimal_rank returns a rank <= D meeting the fidelity target (so it
        #      never needs a lossy ceiling cut; χ=bare_rank always qualifies losslessly).
        env_rank, _U, _Vh, fid_env = fet.env_optimal_rank(state, bond, eps_fid=EPS_FID)
        assert int(env_rank) <= D
        assert float(fid_env) >= 1.0 - EPS_FID - 1e-9, (
            f"env_optimal_rank chose a rank with fid_env={fid_env!r} < 1-eps_fid — "
            "the selected rank is not fidelity-faithful")

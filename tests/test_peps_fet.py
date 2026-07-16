from __future__ import annotations

r"""PEPS environment-aware truncation tests.

The suite checks the exact single-bond environment against an independent dense
contraction, compares ``Fid_Γ`` with an independently written state-overlap
calculation at lossless and lossy points, and verifies the ``fet_env`` policy
wiring. The end-to-end entropy check compares a one-round carrier state with an
inline GF(2) stabilizer reference.  A separate non-degeneracy check requires the
same run to exercise at least one accepted, rank-reducing FET write-back, so an
all-identity/no-op selector cannot make the entropy check pass vacuously.

Tests that construct :class:`PepsState` require CUDA. Tests needing the local d3
Google circuit skip when those files are absent; no synthetic circuit is used as
a fallback. Reference calculations in this file share no implementation path
with ``carrier/peps/fet.py``.
"""

import math

import numpy as np
import pytest
import torch

from _support.fixtures import assert_control_trips, require_precondition

# --------------------------------------------------------------------------- #
# Numerical bars and independent d3 leak-off run constants                    #
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
LEAKAGE_RATE_OFF = 0.0

EPS_SPIKE = 1e-8          # dynamic-epsilon control knob used by the d3 tests
W_MAX = 160
CUT_A = (0, 1, 2, 3)
GROWN_MIN = 5             # a grid bond dim >= this counts as "grown" (over-count present)

EPS_FID = 1e-8            # env-optimal acceptance: smallest χ with Fid_Γ >= 1 - EPS_FID

GAMMA_REL_TOL = 1e-9     # two-route Γ comparison bar
FID_ANTICIRC_TOL = 1e-6  # Fid_Γ == fid_dense comparison bar
SA_BASELINE_LEAKOFF = 2.0   # d3 leak-off GF(2) stabilizer entropy across cut (0,1,2,3)
SA_OFF_TOL = 1e-4        # leak-off post-trunc S_A deviation bar
NORM_GUARD = 1e-12       # fid_dense norm guard: degenerate truncation gives fidelity 0

_CUDA = torch.cuda.is_available()
requires_cuda = pytest.mark.skipif(
    not _CUDA, reason="CUDA unavailable; the PEPS/FET engine is GPU-only")


# =========================================================================== #
# Runtime adapters for the current PEPS public surface                        #
# =========================================================================== #
_PEPS_PKG = "error_coupling_simulator.carrier.peps"


def _peps_namespaces() -> list:
    """Runtime-only import of the package and all its submodules
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
        f"(update the runtime adapter for the current spelling)")


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


# ---- Source object handles resolved lazily -------------------------------- #
def _TruncationPolicy():
    return _resolve_any(("TruncationPolicy",), "the truncation policy dataclass")


def _trunc_policy(mode: str, **kw):
    """Construct ``TruncationPolicy``; ``fet_env`` requires ``eps_fid``."""
    TP = _TruncationPolicy()
    return TP(str(mode), **kw)


def _PepsSampler():
    return _resolve_any(("PepsSampler",), "the PEPS trajectory sampler")


def _build_codestate(sched, m: int):
    fn = _resolve_any(("build_codestate_peps",), "the codestate builder")
    return _try_calls(
        [lambda: fn(sched, int(m), device="cuda"),
         lambda: fn(sched, int(m), "cuda"),
         lambda: fn(sched, int(m))],
        "build_codestate_peps")


def _dense_psi(state) -> torch.Tensor:
    """Bounded d3 ``dense_psi(state)`` bridge; engine position 0 is the MSB."""
    fn = _resolve("dense_psi")
    if fn is not None:
        return torch.as_tensor(fn(state)).reshape(-1)
    meth = getattr(state, "dense_psi", None)
    if callable(meth):
        return torch.as_tensor(meth()).reshape(-1)
    pytest.fail("carrier/peps exposes no dense_psi; fix this adapter")


def _bond_profile(state) -> dict:
    fn = _resolve_any(("bond_profile",), "the bond profile")
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
    fn = _resolve_any(("site_tensor",), "the Q{pos} site accessor")
    return fn(state, int(pos))


def _phys_name(pos: int) -> str:
    fn = _resolve_any(("phys_name",), "the physical index name")
    return str(fn(int(pos)))


# ---- FET surface ----------------------------------------------------------- #
def _fet_gamma_TN(state, bond: str) -> torch.Tensor:
    """Exact double-layer single-bond ``Γ[i,I,j,J]``."""
    fn = _resolve_any(("gamma_TN",), "the exact single-bond environment Γ")
    out = _try_calls([lambda: fn(state, str(bond))], "gamma_TN")
    return torch.as_tensor(out)


def _fet_gamma_fidelity(Gamma: torch.Tensor, M: torch.Tensor) -> float:
    """The Γ-metric fidelity of bond map ``M``."""
    fn = _resolve_any(("gamma_fidelity",), "the Γ-fidelity")
    return float(_try_calls([lambda: fn(Gamma, M)], "gamma_fidelity"))


def _fet_env_optimal_rank(state, bond: str, eps_fid: float):
    """``env_optimal_rank(state, bond, eps_fid)`` -> (env_rank, U, Vh).

    Normalizes the return to ``(env_rank:int, U, Vh)`` (dropping any trailing
    achieved-fidelity element); accepts a 4-tuple ``(env_rank, U, Vh, fid_env)``, a
    3-tuple, a ``(env_rank, (U, Vh))`` pair, or a dict. The fallback may
    carry ``U``/``Vh`` = None — the caller only asserts on ``env_rank`` there."""
    fn = _resolve_any(("env_optimal_rank",), "the env-optimal rank selector")
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
    """Pass-1 seam whose ``fet_env`` branch must be a strict no-op."""
    fn = _resolve_any(("_policy_precut",), "the pass-1 precut seam")
    return fn(state, str(bond), policy)


def _insertion_spectrum(state, bond: str) -> torch.Tensor:
    fn = _resolve_any(("_insertion_spectrum",), "the pair-insertion spectrum")
    return torch.as_tensor(fn(state, str(bond)))


def _exact_rank(S: torch.Tensor) -> int:
    fn = _resolve_any(("_exact_rank",), "the exact-local-rank helper")
    return int(fn(torch.as_tensor(S)))


# =========================================================================== #
# Independent references sharing no implementation path with fet.py           #
#   * GF(2) stabilizer entropy: independent inline diagnostic                 #
#     (import NOTHING from the carrier).                                       #
#   * carrier_SA: the carrier's OWN dense S_A read (routed through the adapter #
#     dense_psi — the only adapter used by that independent calculation).      #
#   * Γ_dense / fid_dense / write-back: independent two-route references.     #
# =========================================================================== #
def _gf2_rank(rows: list) -> int:
    """Rank over GF(2) of bit-vectors packed as Python integers."""
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
    """A stabilizer/logical ``{site: 'X'|'Z'}`` -> (x_bits, z_bits)."""
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
    """S_A (ebits) of the pure stabilizer state by Fattal/Hamma, computed with
    pure GF(2) algebra independent of the carrier and Stim."""
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
    """``B{a}_{b}`` -> (a, b) with a < b."""
    body = str(bond)[1:]
    a_str, b_str = body.split("_")
    a, b = int(a_str), int(b_str)
    return (a, b) if a < b else (b, a)


def _gamma_dense_ref(state, bond: str) -> torch.Tensor:
    """Independent reference route for Γ[i,I,j,J] (shares no code with the source
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
    """Independent reference write-back: absorb ``U`` (D×χ)
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
    copy using the independent write-back, recompute ``dense_psi``, and measure
    |<before|after>|^2.
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
        solve_exchange_angle_for_leakage_rate,
    )

    theta = solve_exchange_angle_for_leakage_rate(LEAKAGE_RATE_OFF, g_seep=G_SEEP, g_heat=G_HEAT)
    return RunSpec(circuit_path=c01, metadata_path=m01, m=LOGICAL_M, theta=float(theta),
                   g_seep=G_SEEP, g_heat=G_HEAT, arm=ARM, b=B_BIAS, readout_conv=READOUT_CONV,
                   N=1, base_seed=int(base_seed), R=int(R), dtype="c128")


def _drive_capture(
    sched,
    c01,
    m01,
    policy,
    *,
    d_abort,
    capture_round: int = 0,
    return_ledgers: bool = False,
):
    """Drive ONE leak-off trajectory (EXACT route) under ``policy`` and return the
    live PepsState snapshot captured after round ``capture_round`` (a ``.copy()``)."""
    spec = _build_spec(c01, m01, R=capture_round + 1, base_seed=BASE_SEED_OFF)
    Sampler = _PepsSampler()
    captured: dict = {}

    def hook(st, r, shot):
        if int(r) == int(capture_round):
            captured["state"] = st.copy()

    _shotset, ledgers = Sampler(device="cuda").sample(
        spec, sched=sched, policy=policy, R_n=None, R_x=None, fit_seed=FIT_SEED,
        materialize=True, d_abort=d_abort, round_hook=hook)
    state = captured.get("state")
    if return_ledgers:
        return state, ledgers
    return state


@pytest.fixture(scope="module")
def d3():
    """The REAL d3_at_q6_7 leak-off schedule + r10 within-cycle streams."""
    if not _CUDA:
        pytest.skip("CUDA unavailable; the PEPS engine is GPU-only")
    return _parse_d3_sched()


@pytest.fixture(scope="module")
def gf2_baseline(d3):
    """The INDEPENDENT GF(2) stabilizer-entropy baseline across cut A (== 2.0 ebits
    at d3 leak-off) computed from the schedule's generators."""
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
                         f"no grown bond (dim >= {GROWN_MIN}) after round 1")
    return st


@pytest.fixture(scope="module")
def fet_env_run(d3):
    """One shared ``fet_env`` drive, including its state and mutation ledger."""
    sched, c01, m01 = d3
    st, ledgers = _drive_capture(
        sched,
        c01,
        m01,
        _trunc_policy("fet_env", eps_fid=EPS_FID),
        d_abort=None,
        return_ledgers=True,
    )
    require_precondition(st is not None, "no round-1 state captured (fet_env drive)")
    require_precondition(len(ledgers) == 1, f"expected one FET ledger, got {len(ledgers)}")
    return st, ledgers[0]


@pytest.fixture(scope="module")
def fet_env_state(fet_env_run):
    """State component of the shared strict-``eps_fid`` ``fet_env`` drive."""

    return fet_env_run[0]


def _biggest_grown_bond(state):
    grown = _grown_bonds(state)
    require_precondition(bool(grown), f"no grown bond (dim >= {GROWN_MIN})")
    bond, dim = max(grown, key=lambda bd: bd[1])
    return bond, int(dim)


# =========================================================================== #
# Two-route Γ and fidelity checks on a real round-1 bond                      #
# =========================================================================== #
@requires_cuda
class TestEnvironmentCrossChecks:

    def test_gamma_two_route_identity(self, grown_state):
        """Γ_TN (source) equals the independent dense reference on the biggest
        grown bond to 1e-9. A 1e-6 perturbation must trip the same check."""
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
        # A 1e-6-perturbed reference Γ must trip the 1e-9 check.
        assert_control_trips(_two_route, g_ref * (1.0 + 1e-6), GAMMA_REL_TOL)

    def test_fid_gamma_equals_fid_dense(self, grown_state):
        """Fid_Γ (source Γ-metric) equals the independent dense overlap on the same
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
# Post-fet_env S_A against the inline GF(2) baseline                          #
# =========================================================================== #
@requires_cuda
class TestStabilizerEntropy:

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

        # Positive for the entropy observable only.  The separate non-degeneracy
        # gate must still prove that this run actually applied a FET truncation.
        _sa_matches(gf2_baseline, SA_OFF_TOL)
        # control: a reference offset by 10·tol MUST trip (the tolerance is discriminating).
        assert_control_trips(_sa_matches, gf2_baseline + 10.0 * SA_OFF_TOL, SA_OFF_TOL)


# =========================================================================== #
# fet_env wiring: precut no-op, end-to-end drive, and full-rank losslessness  #
# =========================================================================== #
@requires_cuda
class TestFetEnvWiring:

    def test_fet_env_exercises_an_accepted_rank_reducing_writeback(self, fet_env_run):
        """The entropy fixture must not pass through an all-identity/no-op path."""
        _state, ledger = fet_env_run
        cuts = [entry for entry in ledger if entry.get("op") == "fet_truncate"]
        require_precondition(cuts, "fet_env drive emitted no FET cut ledger rows")
        applied = [entry for entry in cuts if bool(entry.get("writeback_applied"))]
        cut_diagnostics = [
            {
                key: entry.get(key)
                for key in (
                    "bond",
                    "dim_in",
                    "dim_out",
                    "selected_env_rank",
                    "proposed_env_rank",
                    "Fid_gamma",
                    "selected_Fid_gamma",
                    "outcome",
                    "reason",
                    "map_valid",
                    "selector_outcome",
                    "solver_failure_count",
                    "attempted_ranks",
                )
            }
            for entry in cuts
        ]
        assert applied, (
            "fet_env entropy fixture applied no rank-reducing FET map; "
            "an all-identity/no-op run cannot certify truncation fidelity; "
            f"cuts={cut_diagnostics!r}"
        )
        for entry in applied:
            assert entry["outcome"] == "accepted", entry
            assert entry["reason"] == "fidelity_target_met", entry
            assert bool(entry["selected_fidelity_valid"]), entry
            assert bool(entry["selected_target_met"]), entry
            assert bool(entry["selector_consistent"]), entry
            assert bool(entry["map_valid"]), entry
            assert 0 < int(entry["dim_out"]) < int(entry["dim_in"]), entry
            assert int(entry["env_rank"]) == int(entry["dim_out"]), entry
            assert int(entry["selected_env_rank"]) == int(entry["dim_out"]), entry

    def test_fet_env_drives_one_round_without_crashing(self, fet_env_state):
        """``TruncationPolicy("fet_env", eps_fid=1e-8)`` drove one
        round via ``PepsSampler.sample`` and returned a live PepsState with a readable
        grid bond profile (a fall-through to the dynamic_eps tail would have raised
        ``float(None)``)."""
        prof = _bond_profile(fet_env_state)
        assert prof, "fet_env round produced no grid bond profile"
        assert all(int(d) >= 1 for d in prof.values()), prof
        # The fet_env round yields a finite, materialized state.
        psi = _dense_psi(fet_env_state)
        assert torch.isfinite(psi).all(), "fet_env round produced a non-finite state"
        assert float(torch.vdot(psi, psi).real) > 1e-12, "fet_env round collapsed the norm"

    def test_policy_precut_is_a_strict_noop_for_fet_env(self, grown_state):
        """``_policy_precut`` for ``fet_env`` returns the exact summary
        keys ``_policy_cut`` reads (precut_discarded == 0.0, r_dyn/width None,
        window_binding False, exact_rank == _exact_rank(_insertion_spectrum)) and does
        NO svd (bond dim UNCHANGED). Control: ``dynamic_eps`` populates r_dyn/width
        (the None-signature is fet_env-specific — the assertions are not vacuous)."""
        bond, dim = _biggest_grown_bond(grown_state)

        pol = _trunc_policy("fet_env", eps_fid=EPS_FID)
        # fet_env carries no eps_spike, so a fall-through to
        # the dynamic tail would evaluate float(policy.eps_spike) == float(None).
        assert getattr(pol, "eps_spike", None) is None, (
            "fet_env policy unexpectedly carries eps_spike")

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
        """The no-qualifying-χ fallback
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
            "— the keep-full-bond fallback would then not be safe")
        # (ii) env_optimal_rank returns a rank <= D meeting the fidelity target (so it
        #      never needs a lossy ceiling cut; χ=bare_rank always qualifies losslessly).
        env_rank, _U, _Vh, fid_env = fet.env_optimal_rank(state, bond, eps_fid=EPS_FID)
        assert int(env_rank) <= D
        assert float(fid_env) >= 1.0 - EPS_FID - 1e-9, (
            f"env_optimal_rank chose a rank with fid_env={fid_env!r} < 1-eps_fid — "
            "the selected rank is not fidelity-faithful")


# =========================================================================== #
# FET mutation-boundary firewall                                               #
# =========================================================================== #
class _FakeBondNetwork:
    def __init__(self, bond: str, dim: int) -> None:
        self._dims = {str(bond): int(dim)}

    def ind_size(self, bond: str) -> int:
        return int(self._dims[str(bond)])


class _FakeFetState:
    def __init__(self, bond: str, dim: int) -> None:
        self.tn = _FakeBondNetwork(bond, dim)
        self.device = "cpu"
        self.ledger: list[dict] = []


@pytest.mark.parametrize(
    ("candidate_fid", "expected_outcome"),
    [
        (0.98, "solver_failed"),
        (-1.0, "solver_failed"),
        (2.0, "solver_failed"),
        (float("-inf"), "solver_failed"),
        (float("nan"), "solver_failed"),
    ],
)
def test_policy_cut_rejected_fet_candidate_is_a_strict_noop(
    monkeypatch: pytest.MonkeyPatch,
    candidate_fid: float,
    expected_outcome: str,
) -> None:
    """A bare legacy tuple has no authenticated selector outcome or solver
    metadata and must never reach the in-place write-back helper."""
    import importlib

    fet = importlib.import_module(f"{_PEPS_PKG}.fet")
    trajectory = importlib.import_module(f"{_PEPS_PKG}.trajectory")
    bond = "B0_1"
    state = _FakeFetState(bond, dim=2)
    U = torch.ones((2, 1), dtype=torch.complex128)
    Vh = torch.ones((1, 2), dtype=torch.complex128)
    writes: list[tuple[str, tuple[int, ...], tuple[int, ...]]] = []

    monkeypatch.setattr(
        fet,
        "env_optimal_rank",
        lambda _state, _bond, _eps, **_kwargs: (1, U, Vh, candidate_fid),
    )

    def _writeback(_state, _bond, map_u, map_vh) -> None:
        writes.append((str(_bond), tuple(map_u.shape), tuple(map_vh.shape)))
        _state.tn._dims[str(_bond)] = int(map_u.shape[1])

    monkeypatch.setattr(fet, "apply_fet_truncation", _writeback)

    summary = trajectory._policy_cut(
        state,
        bond,
        trajectory.TruncationPolicy("fet_env", eps_fid=0.01),
        {"exact_rank": 1},
    )

    assert writes == []
    assert state.tn.ind_size(bond) == 2
    assert summary["outcome"] == expected_outcome
    assert summary["writeback_applied"] is False
    assert summary["proposed_env_rank"] == 1
    assert summary["env_rank"] == 2
    assert summary["dim_out"] == 2
    assert state.ledger == [summary]


def test_policy_cut_qualifying_fet_candidate_still_reduces_rank(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A qualifying finite control must still reach the write-back seam, proving
    the mutation firewall is selective rather than an unconditional no-op."""
    import importlib

    fet = importlib.import_module(f"{_PEPS_PKG}.fet")
    trajectory = importlib.import_module(f"{_PEPS_PKG}.trajectory")
    bond = "B0_1"
    state = _FakeFetState(bond, dim=2)
    U = torch.ones((2, 1), dtype=torch.complex128)
    Vh = torch.ones((1, 2), dtype=torch.complex128)
    writes: list[str] = []

    accepted = fet.FetSelection(
        1,
        U,
        Vh,
        0.995,
        outcome="accepted",
        candidate_rank=1,
        candidate_fid=0.995,
        solver_seed=0,
        attempted_ranks=1,
        solver_failure_count=0,
    )
    monkeypatch.setattr(
        fet,
        "env_optimal_rank",
        lambda _state, _bond, _eps, **_kwargs: accepted,
    )

    def _writeback(_state, _bond, map_u, _map_vh) -> None:
        writes.append(str(_bond))
        _state.tn._dims[str(_bond)] = int(map_u.shape[1])

    monkeypatch.setattr(fet, "apply_fet_truncation", _writeback)

    summary = trajectory._policy_cut(
        state,
        bond,
        trajectory.TruncationPolicy("fet_env", eps_fid=0.01),
        {"exact_rank": 1},
    )

    assert writes == [bond]
    assert state.tn.ind_size(bond) == 1
    assert summary["outcome"] == "accepted"
    assert summary["writeback_applied"] is True
    assert summary["proposed_env_rank"] == 1
    assert summary["env_rank"] == 1
    assert summary["dim_out"] == 1


def test_policy_cut_rejects_selection_bound_to_wrong_solver_seed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The returned numerical solve must be bound to the policy's requested seed."""
    import importlib

    fet = importlib.import_module(f"{_PEPS_PKG}.fet")
    trajectory = importlib.import_module(f"{_PEPS_PKG}.trajectory")
    bond = "B0_1"
    state = _FakeFetState(bond, dim=2)
    U = torch.ones((2, 1), dtype=torch.complex128)
    Vh = torch.ones((1, 2), dtype=torch.complex128)
    selection = fet.FetSelection(
        1,
        U,
        Vh,
        0.995,
        outcome="accepted",
        candidate_rank=1,
        candidate_fid=0.995,
        solver_seed=8,
        attempted_ranks=1,
        solver_failure_count=0,
    )
    writes: list[str] = []
    monkeypatch.setattr(fet, "env_optimal_rank", lambda *_args, **_kwargs: selection)
    monkeypatch.setattr(
        fet,
        "apply_fet_truncation",
        lambda *_args, **_kwargs: writes.append("called"),
    )

    summary = trajectory._policy_cut(
        state,
        bond,
        trajectory.TruncationPolicy(
            "fet_env", eps_fid=0.01, fet_solver_seed=7
        ),
        {"exact_rank": 1},
    )

    assert writes == []
    assert summary["requested_fet_solver_seed"] == 7
    assert summary["fet_solver_seed"] == 8
    assert summary["solver_seed_consistent"] is False
    assert summary["selector_consistent"] is False
    assert summary["writeback_applied"] is False
    assert summary["outcome"] == "solver_failed"


@pytest.mark.parametrize("collect_curve", [False, True])
def test_env_optimal_rank_no_qualifier_returns_full_identity(
    monkeypatch: pytest.MonkeyPatch,
    collect_curve: bool,
) -> None:
    """Both selector paths must implement their documented full-rank identity
    fallback instead of returning the best rejected low-rank proposal."""
    import importlib

    fet = importlib.import_module(f"{_PEPS_PKG}.fet")
    Gamma = torch.zeros((2, 2, 2, 2), dtype=torch.complex128)
    U = torch.ones((2, 1), dtype=torch.complex128)
    Vh = torch.ones((1, 2), dtype=torch.complex128)

    monkeypatch.setattr(fet, "gamma_TN", lambda _state, _bond: Gamma)
    monkeypatch.setattr(
        fet,
        "_insertion_spectrum",
        lambda _state, _bond: torch.tensor([1.0, 0.0], dtype=torch.float64),
    )
    monkeypatch.setattr(fet, "_exact_rank", lambda _spectrum: 1)
    monkeypatch.setattr(fet, "_fix_gauge", lambda _gamma: None)
    monkeypatch.setattr(
        fet,
        "_multistart_als_truncation",
        lambda _gamma, _state, _bond, _chi, _prep, **_kwargs: {
            "U": U,
            "Vh": Vh,
        },
    )
    monkeypatch.setattr(fet, "gamma_fidelity", lambda _gamma, _map: 0.5)
    curve = [] if collect_curve else None

    selection = fet.env_optimal_rank(
        object(), "B0_1", eps_fid=0.01, fidelity_curve=curve
    )
    rank, map_u, map_vh, fid = selection

    identity = torch.eye(2, dtype=torch.complex128)
    assert rank == 2
    assert torch.equal(map_u, identity)
    assert torch.equal(map_vh, identity)
    assert fid == 1.0
    assert selection.outcome == "noop"
    assert selection.candidate_rank == 1
    assert selection.candidate_fid == 0.5
    if curve is not None:
        assert curve == [{"chi": 1, "fid": 0.5, "solver_status": "ok"}]


def test_env_optimal_rank_all_nonfinite_is_explicit_solver_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """All-nonfinite optimization is not a finite ``-1`` candidate."""
    import importlib

    fet = importlib.import_module(f"{_PEPS_PKG}.fet")
    Gamma = torch.zeros((2, 2, 2, 2), dtype=torch.complex128)
    U = torch.ones((2, 1), dtype=torch.complex128)
    Vh = torch.ones((1, 2), dtype=torch.complex128)
    monkeypatch.setattr(fet, "gamma_TN", lambda _state, _bond: Gamma)
    monkeypatch.setattr(
        fet,
        "_insertion_spectrum",
        lambda _state, _bond: torch.tensor([1.0, 0.0], dtype=torch.float64),
    )
    monkeypatch.setattr(fet, "_exact_rank", lambda _spectrum: 1)
    monkeypatch.setattr(fet, "_fix_gauge", lambda _gamma: None)
    monkeypatch.setattr(
        fet,
        "_multistart_als_truncation",
        lambda _gamma, _state, _bond, _chi, _prep, **_kwargs: {
            "U": U,
            "Vh": Vh,
        },
    )
    monkeypatch.setattr(
        fet, "gamma_fidelity", lambda _gamma, _map: float("-inf")
    )
    curve: list[dict] = []

    selection = fet.env_optimal_rank(
        object(), "B0_1", eps_fid=0.01, fidelity_curve=curve
    )
    rank, map_u, map_vh, applied_fid = selection

    identity = torch.eye(2, dtype=torch.complex128)
    assert rank == 2
    assert torch.equal(map_u, identity)
    assert torch.equal(map_vh, identity)
    assert applied_fid == 1.0
    assert selection.outcome == "solver_failed"
    assert selection.candidate_rank is None
    assert selection.candidate_fid is None
    assert curve == [{"chi": 1, "fid": None, "solver_status": "solver_failed"}]


def test_env_optimal_rank_never_rescores_solver_failed_placeholder_as_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A finite score for a failure placeholder cannot authorize write-back."""
    import importlib

    fet = importlib.import_module(f"{_PEPS_PKG}.fet")
    Gamma = torch.zeros((2, 2, 2, 2), dtype=torch.complex128)
    U = torch.tensor([[1.0], [0.0]], dtype=torch.complex128)
    Vh = torch.tensor([[1.0, 0.0]], dtype=torch.complex128)
    monkeypatch.setattr(fet, "gamma_TN", lambda _state, _bond: Gamma)
    monkeypatch.setattr(
        fet,
        "_insertion_spectrum",
        lambda _state, _bond: torch.tensor([1.0, 0.0], dtype=torch.float64),
    )
    monkeypatch.setattr(fet, "_exact_rank", lambda _spectrum: 1)
    monkeypatch.setattr(fet, "_fix_gauge", lambda _gamma: None)
    monkeypatch.setattr(
        fet,
        "_multistart_als_truncation",
        lambda _gamma, _state, _bond, _chi, _prep, **_kwargs: {
            "U": U,
            "Vh": Vh,
            "fid": float("-inf"),
            "solver_status": "solver_failed",
        },
    )
    # The placeholder itself happens to score perfectly.  Its solver status is
    # still authoritative and must prevent it from becoming a candidate.
    monkeypatch.setattr(fet, "gamma_fidelity", lambda _gamma, _map: 1.0)

    selection = fet.env_optimal_rank(object(), "B0_1", eps_fid=0.01)

    identity = torch.eye(2, dtype=torch.complex128)
    assert selection.outcome == "solver_failed"
    assert selection.env_rank == 2
    assert torch.equal(selection.U, identity)
    assert torch.equal(selection.Vh, identity)
    assert selection.candidate_rank is None
    assert selection.candidate_fid is None


def test_apply_fet_truncation_rolls_back_first_tensor_if_second_modify_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The two-site write-back is transactional across both bond endpoints."""
    import importlib

    fet = importlib.import_module(f"{_PEPS_PKG}.fet")

    class _FakeTensor:
        def __init__(self, data: torch.Tensor, *, fail_modify: bool = False) -> None:
            self.data = data
            self.inds = ("B0_1",)
            self.fail_modify = fail_modify

        def modify(self, *, data: torch.Tensor) -> None:
            if self.fail_modify:
                self.fail_modify = False
                raise RuntimeError("injected second-site modify failure")
            self.data = data

    original_a = torch.tensor([1.0, 2.0], dtype=torch.complex128)
    original_b = torch.tensor([3.0, 4.0], dtype=torch.complex128)
    tensor_a = _FakeTensor(original_a.clone())
    tensor_b = _FakeTensor(original_b.clone(), fail_modify=True)
    monkeypatch.setattr(
        fet,
        "site_tensor",
        lambda _state, site: tensor_a if int(site) == 0 else tensor_b,
    )
    U = torch.tensor([[1.0], [0.0]], dtype=torch.complex128)
    Vh = torch.tensor([[1.0, 0.0]], dtype=torch.complex128)

    with pytest.raises(RuntimeError, match="injected second-site"):
        fet.apply_fet_truncation(object(), "B0_1", U, Vh)

    assert torch.equal(tensor_a.data, original_a)
    assert torch.equal(tensor_b.data, original_b)


@pytest.mark.parametrize("failing_site", [0, 1])
def test_apply_fet_truncation_rolls_back_mutate_then_raise_on_either_endpoint(
    monkeypatch: pytest.MonkeyPatch,
    failing_site: int,
) -> None:
    """Rollback restores both snapshots even if modify mutates before raising."""
    import importlib

    fet = importlib.import_module(f"{_PEPS_PKG}.fet")

    class _FakeTensor:
        def __init__(self, data: torch.Tensor, *, fail_once: bool = False) -> None:
            self.data = data
            self.inds = ("B0_1",)
            self.fail_once = fail_once

        def modify(self, *, data: torch.Tensor) -> None:
            self.data = data
            if self.fail_once:
                self.fail_once = False
                raise RuntimeError("injected mutate-then-raise")

    originals = [
        torch.tensor([1.0, 2.0], dtype=torch.complex128),
        torch.tensor([3.0, 4.0], dtype=torch.complex128),
    ]
    tensors = [
        _FakeTensor(original.clone(), fail_once=index == failing_site)
        for index, original in enumerate(originals)
    ]
    monkeypatch.setattr(fet, "site_tensor", lambda _state, site: tensors[int(site)])
    U = torch.tensor([[1.0], [0.0]], dtype=torch.complex128)
    Vh = torch.tensor([[1.0, 0.0]], dtype=torch.complex128)

    with pytest.raises(RuntimeError, match="mutate-then-raise"):
        fet.apply_fet_truncation(object(), "B0_1", U, Vh)

    assert all(
        torch.equal(tensor.data, original)
        for tensor, original in zip(tensors, originals, strict=True)
    )


def test_apply_fet_truncation_rejects_nonfinite_absorption_before_writeback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Finite factors may still overflow; derived tensors must be authenticated."""
    import importlib

    fet = importlib.import_module(f"{_PEPS_PKG}.fet")

    class _FakeTensor:
        def __init__(self, data: torch.Tensor) -> None:
            self.data = data
            self.inds = ("B0_1",)
            self.modify_calls = 0

        def modify(self, *, data: torch.Tensor) -> None:
            self.modify_calls += 1
            self.data = data

    tensors = [
        _FakeTensor(torch.tensor([1.0e308, 1.0e308], dtype=torch.complex128)),
        _FakeTensor(torch.tensor([1.0, 1.0], dtype=torch.complex128)),
    ]
    monkeypatch.setattr(fet, "site_tensor", lambda _state, site: tensors[int(site)])
    U = torch.tensor([[1.0e308], [1.0e308]], dtype=torch.complex128)
    Vh = torch.tensor([[1.0e-308, 1.0e-308]], dtype=torch.complex128)

    with pytest.raises(RuntimeError, match="non-finite absorption"):
        fet.apply_fet_truncation(object(), "B0_1", U, Vh)

    assert [tensor.modify_calls for tensor in tensors] == [0, 0]


@pytest.mark.parametrize(
    ("left_dim", "right_dim", "u_shape", "vh_shape", "message"),
    [
        (2, 2, (2, 1), (2, 2), "shared positive kept rank"),
        (2, 2, (3, 1), (1, 2), "original endpoint dimensions"),
        (2, 3, (2, 1), (1, 3), "endpoint bond dimensions"),
    ],
)
def test_apply_fet_truncation_rejects_cross_endpoint_shape_corruption_before_writeback(
    monkeypatch: pytest.MonkeyPatch,
    left_dim: int,
    right_dim: int,
    u_shape: tuple[int, int],
    vh_shape: tuple[int, int],
    message: str,
) -> None:
    import importlib

    fet = importlib.import_module(f"{_PEPS_PKG}.fet")

    class _FakeTensor:
        def __init__(self, dim: int) -> None:
            self.data = torch.ones(dim, dtype=torch.complex128)
            self.inds = ("B0_1",)
            self.modify_calls = 0

        def modify(self, *, data: torch.Tensor) -> None:
            self.modify_calls += 1
            self.data = data

    tensors = [_FakeTensor(left_dim), _FakeTensor(right_dim)]
    originals = [tensor.data.clone() for tensor in tensors]
    monkeypatch.setattr(fet, "site_tensor", lambda _state, site: tensors[int(site)])
    U = torch.ones(u_shape, dtype=torch.complex128)
    Vh = torch.ones(vh_shape, dtype=torch.complex128)

    with pytest.raises((ValueError, RuntimeError), match=message):
        fet.apply_fet_truncation(object(), "B0_1", U, Vh)

    assert [tensor.modify_calls for tensor in tensors] == [0, 0]
    assert all(
        torch.equal(tensor.data, original)
        for tensor, original in zip(tensors, originals, strict=True)
    )


def test_policy_cut_rejects_inconsistent_accepted_selector_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Rejected-candidate attributes cannot override the selected tuple score."""
    import importlib

    fet = importlib.import_module(f"{_PEPS_PKG}.fet")
    trajectory = importlib.import_module(f"{_PEPS_PKG}.trajectory")
    bond = "B0_1"
    state = _FakeFetState(bond, dim=2)
    U = torch.ones((2, 1), dtype=torch.complex128)
    Vh = torch.ones((1, 2), dtype=torch.complex128)
    inconsistent = fet.FetSelection(
        1,
        U,
        Vh,
        float("-inf"),
        outcome="accepted",
        candidate_rank=1,
        candidate_fid=0.995,
        solver_seed=0,
        attempted_ranks=1,
        solver_failure_count=0,
    )
    writes: list[str] = []
    monkeypatch.setattr(
        fet, "env_optimal_rank", lambda *_args, **_kwargs: inconsistent
    )
    monkeypatch.setattr(
        fet,
        "apply_fet_truncation",
        lambda *_args, **_kwargs: writes.append("called"),
    )

    summary = trajectory._policy_cut(
        state,
        bond,
        trajectory.TruncationPolicy("fet_env", eps_fid=0.01),
        {"exact_rank": 1},
    )

    assert writes == []
    assert summary["selector_consistent"] is False
    assert summary["selected_fidelity_valid"] is False
    assert summary["writeback_applied"] is False
    assert summary["outcome"] == "solver_failed"


def test_policy_cut_rejects_map_on_wrong_state_device(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Map health includes the carrier device, not only U/Vh agreement."""
    import importlib

    fet = importlib.import_module(f"{_PEPS_PKG}.fet")
    trajectory = importlib.import_module(f"{_PEPS_PKG}.trajectory")
    bond = "B0_1"
    state = _FakeFetState(bond, dim=2)
    state.device = "cuda"
    U = torch.ones((2, 1), dtype=torch.complex128, device="cpu")
    Vh = torch.ones((1, 2), dtype=torch.complex128, device="cpu")
    writes: list[str] = []
    monkeypatch.setattr(
        fet,
        "env_optimal_rank",
        lambda _state, _bond, _eps, **_kwargs: (1, U, Vh, 0.995),
    )
    monkeypatch.setattr(
        fet,
        "apply_fet_truncation",
        lambda *_args, **_kwargs: writes.append("called"),
    )

    summary = trajectory._policy_cut(
        state,
        bond,
        trajectory.TruncationPolicy("fet_env", eps_fid=0.01),
        {"exact_rank": 1},
    )

    assert writes == []
    assert summary["map_device_ok"] is False
    assert summary["map_valid"] is False
    assert summary["writeback_applied"] is False


def test_fidelity_curve_observation_cannot_change_first_accepted_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Full-curve diagnostics may do extra work but must freeze the fast result."""
    import importlib

    fet = importlib.import_module(f"{_PEPS_PKG}.fet")
    Gamma = torch.zeros((2, 2, 2, 2), dtype=torch.complex128)
    maps = {
        1: (
            torch.tensor([[1.0], [0.0]], dtype=torch.complex128),
            torch.tensor([[0.995, 0.0]], dtype=torch.complex128),
        ),
        2: (
            torch.eye(2, dtype=torch.complex128),
            torch.eye(2, dtype=torch.complex128),
        ),
    }
    monkeypatch.setattr(fet, "gamma_TN", lambda _state, _bond: Gamma)
    monkeypatch.setattr(
        fet,
        "_insertion_spectrum",
        lambda _state, _bond: torch.tensor([1.0, 1.0], dtype=torch.float64),
    )
    monkeypatch.setattr(fet, "_exact_rank", lambda _spectrum: 2)
    monkeypatch.setattr(fet, "_fix_gauge", lambda _gamma: None)
    monkeypatch.setattr(
        fet,
        "_multistart_als_truncation",
        lambda _gamma, _state, _bond, chi, _prep, **_kwargs: {
            "U": maps[int(chi)][0],
            "Vh": maps[int(chi)][1],
            "solver_status": "ok" if int(chi) == 1 else "solver_failed",
        },
    )
    monkeypatch.setattr(
        fet,
        "gamma_fidelity",
        lambda _gamma, map_tensor: 0.995
        if torch.count_nonzero(map_tensor).item() == 1
        else 1.0,
    )

    fast = fet.env_optimal_rank(object(), "B0_1", eps_fid=0.01)
    curve: list[dict] = []
    observed = fet.env_optimal_rank(
        object(), "B0_1", eps_fid=0.01, fidelity_curve=curve
    )

    assert fast.outcome == observed.outcome == "accepted"
    assert fast.env_rank == observed.env_rank == 1
    assert torch.equal(fast.U @ fast.Vh, observed.U @ observed.Vh)
    assert fast.fid_env == observed.fid_env == 0.995
    assert fast.attempted_ranks == observed.attempted_ranks == 1
    assert fast.solver_failure_count == observed.solver_failure_count == 0
    assert [entry["chi"] for entry in curve] == [1, 2]
    assert curve[1]["solver_status"] == "solver_failed"


def test_policy_cut_nonfinite_map_with_qualifying_fidelity_is_noop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A stale scalar score cannot authorize a non-finite map write-back."""
    import importlib

    fet = importlib.import_module(f"{_PEPS_PKG}.fet")
    trajectory = importlib.import_module(f"{_PEPS_PKG}.trajectory")
    bond = "B0_1"
    state = _FakeFetState(bond, dim=2)
    U = torch.tensor([[complex(float("nan"), 0.0)], [1.0]], dtype=torch.complex128)
    Vh = torch.ones((1, 2), dtype=torch.complex128)
    writes: list[str] = []

    monkeypatch.setattr(
        fet,
        "env_optimal_rank",
        lambda _state, _bond, _eps, **_kwargs: (1, U, Vh, 0.995),
    )
    monkeypatch.setattr(
        fet,
        "apply_fet_truncation",
        lambda *_args, **_kwargs: writes.append("called"),
    )

    summary = trajectory._policy_cut(
        state,
        bond,
        trajectory.TruncationPolicy("fet_env", eps_fid=0.01),
        {"exact_rank": 1},
    )

    assert writes == []
    assert summary["outcome"] == "solver_failed"
    assert summary["map_finite"] is False
    assert summary["writeback_applied"] is False


def test_als_fluctuation_requires_private_generator() -> None:
    """The fluctuation path must never silently fall back to ambient Torch RNG."""
    import importlib

    fet = importlib.import_module(f"{_PEPS_PKG}.fet")
    Gamma = torch.eye(4, dtype=torch.complex128).reshape(2, 2, 2, 2)
    U0 = torch.eye(2, dtype=torch.complex128)[:, :1]

    with pytest.raises(ValueError, match="private generator"):
        fet._als_inner(Gamma, 1, U0, trials=1, fluct=True)


def test_als_private_generator_does_not_advance_ambient_cpu_rng() -> None:
    """A solver kick consumes only its private stream."""
    import importlib

    fet = importlib.import_module(f"{_PEPS_PKG}.fet")
    Gamma = torch.eye(4, dtype=torch.complex128).reshape(2, 2, 2, 2)
    U0 = torch.eye(2, dtype=torch.complex128)[:, :1]
    private = torch.Generator(device="cpu")
    private.manual_seed(17)
    torch.manual_seed(1234)
    before = torch.random.get_rng_state().clone()

    fet._als_inner(
        Gamma, 1, U0, trials=1, fluct=True, generator=private
    )

    assert torch.equal(torch.random.get_rng_state(), before)


@requires_cuda
def test_als_private_generator_does_not_advance_ambient_cuda_rng() -> None:
    """The production-device fluctuation path leaves default CUDA RNG untouched."""
    import importlib

    fet = importlib.import_module(f"{_PEPS_PKG}.fet")
    device = torch.device("cuda")
    Gamma = torch.eye(4, dtype=torch.complex128, device=device).reshape(2, 2, 2, 2)
    U0 = torch.eye(2, dtype=torch.complex128, device=device)[:, :1]
    private = fet._private_solver_generator(
        device,
        solver_seed=7,
        bond="B0_1",
        chi=1,
        restart_name="rand",
    )
    torch.cuda.manual_seed_all(4321)
    before = torch.cuda.get_rng_state(device).clone()

    fet._als_inner(
        Gamma, 1, U0, trials=1, fluct=True, generator=private
    )
    torch.cuda.synchronize(device)

    assert torch.equal(torch.cuda.get_rng_state(device), before)


@requires_cuda
def test_als_result_is_independent_of_ambient_cuda_seed() -> None:
    """Fixed solver coordinates give the same map under another ambient seed."""
    import importlib

    fet = importlib.import_module(f"{_PEPS_PKG}.fet")
    device = torch.device("cuda")
    Gamma = torch.eye(4, dtype=torch.complex128, device=device).reshape(2, 2, 2, 2)
    U0 = torch.eye(2, dtype=torch.complex128, device=device)[:, :1]

    outputs = []
    for ambient_seed in (11, 987654):
        torch.cuda.manual_seed_all(ambient_seed)
        private = fet._private_solver_generator(
            device,
            solver_seed=7,
            bond="B0_1",
            chi=1,
            restart_name="rand",
        )
        U, Vh, fid = fet._als_inner(
            Gamma, 1, U0, trials=1, fluct=True, generator=private
        )
        torch.cuda.synchronize(device)
        outputs.append((U @ Vh, fid))

    assert torch.equal(outputs[0][0], outputs[1][0])
    assert outputs[0][1] == outputs[1][1]


@pytest.mark.parametrize("device", ["cpu", "cuda"])
def test_full_env_selector_does_not_advance_ambient_torch_rng(
    monkeypatch: pytest.MonkeyPatch,
    device: str,
) -> None:
    """Cover generator construction, seed building, and the complete selector."""
    if device == "cuda" and not torch.cuda.is_available():
        pytest.skip("CUDA unavailable")
    import importlib

    fet = importlib.import_module(f"{_PEPS_PKG}.fet")
    Gamma = torch.eye(4, dtype=torch.complex128, device=device).reshape(2, 2, 2, 2)
    spectrum = torch.tensor([1.0, 0.0], dtype=torch.float64, device=device)
    monkeypatch.setattr(fet, "gamma_TN", lambda _state, _bond: Gamma)
    monkeypatch.setattr(fet, "_insertion_spectrum", lambda _state, _bond: spectrum)
    monkeypatch.setattr(fet, "_exact_rank", lambda _spectrum: 1)
    monkeypatch.setattr(
        fet,
        "_carrier_svd_seed",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("unavailable")),
    )
    if device == "cuda":
        torch.cuda.synchronize()
    cpu_before = torch.random.get_rng_state().clone()
    cuda_before = [state.clone() for state in torch.cuda.get_rng_state_all()]

    fet.env_optimal_rank(object(), "B0_1", eps_fid=0.01, solver_seed=7)

    if device == "cuda":
        torch.cuda.synchronize()
    assert torch.equal(cpu_before, torch.random.get_rng_state())
    cuda_after = torch.cuda.get_rng_state_all()
    assert len(cuda_before) == len(cuda_after)
    assert all(
        torch.equal(before, after)
        for before, after in zip(cuda_before, cuda_after, strict=True)
    )

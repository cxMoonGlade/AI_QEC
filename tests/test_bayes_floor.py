"""Executable ledger for the estimable Bayes floor (``qec_twin.audit.bayes_floor``).

Authority: ``docs/nonpauli_teacher/p7b_estimable_floor.md`` §4 (the L1–L6 constraint ledger)
+ ``docs/FAITHFULNESS_PROTOCOL.md`` (the three anti-toy rules). Each ledger item is an
EXECUTABLE test that must FAIL LOUDLY when violated, and EACH is paired with a POSITIVE
CONTROL that confirms the check actually trips on a broken input (Rule II — a check that cannot
fail is not a check).

The ledger this file enforces (the floor estimator's invariants):
  L1 — ``mc_floor(R=1) == enumerate_floor(R=1)`` within 3·MC-SE, validated against a FROM-SCRATCH
       enumerator written IN THIS TEST (raw numpy; shares NO code with bayes_floor / QutritDM —
       the INDEPENDENT ground truth, Rule I). A check vs the engine's own ``min`` is NOT
       certification; this enumerator is the independent reconstruction.
  L2 — convergence / no-drift: ``mc_floor`` slope ≈ 0 within SE; the in-sample PLUG-IN slope > 0
       (the positive control that the tripwire fires — the down-bias rises with N).
  L3 — ``plugin ≤ mc ≤ crossfit`` within SE (MC lands inside the valid bracket).
  L6 — probability sanity along paths: ``0 ≤ P(s,f)``; ``P(s,0)+P(s,1)=P(s)``; sampled
       ``Σ P(s)=1``; CPTP residual < 1e-9 (per-path trace conservation).
  Observable alignment (the L5 hook OWNED here per the brief): the floor's logical PROJECTOR
       matches the teacher's logical observable m — asserted directly against the engine codestate.

GPU-only: the floor model-compute requires CUDA; these cases skip (not fail) without it. The
real d3 geometry is the shipped ``d3_at_q6_7`` r01 patch (skip if absent). The floor is exercised
on a FEASIBLE sub-register (the L1/L2/L3/L6 invariants are register-agnostic; the full 3^9 value
is the decision harness's job, not a unit test).

Run:  conda run -n aiqec python -m pytest -q tests/test_bayes_floor.py
"""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import numpy as np
import pytest

from qec_twin.forward.exact import xzzx_parser as xp

try:
    import torch
    _HAS_CUDA = torch.cuda.is_available()
except Exception:  # noqa: BLE001
    torch = None
    _HAS_CUDA = False

_DATASET = Path(
    "/home/cx/Document/google_105Q_surface_code_d3_d5_d7/google_105Q_surface_code_d3_d5_d7")
_R01_CIRC, _R01_META = xp.default_r01_paths()
_R10_CIRC, _R10_META = xp.default_r10_paths()
_HAS_DATA = _R01_CIRC.is_file() and _R01_META.is_file() and _R10_CIRC.is_file()

requires_cuda = pytest.mark.skipif(not _HAS_CUDA, reason="GPU-only: CUDA not available")
requires_data = pytest.mark.skipif(not _HAS_DATA, reason="shipped d3_at_q6_7 r01/r10 patch absent")

# import the floor-harness helpers (sub-register builder + leak slice) from outputs/ (scripted-
# execution discipline). These build the PROBLEM instance; the floor logic under test is in
# qec_twin.audit.bayes_floor (the src/ module).
_RGT1 = Path(__file__).resolve().parents[1] / "outputs" / "teacher_prereg" / "p7_floor_rgt1.py"


def _load_rgt1():
    import sys
    sys.path.insert(0, str(_RGT1.parent))  # sibling imports inside p7_floor_rgt1
    spec = importlib.util.spec_from_file_location("p7_floor_rgt1", _RGT1)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# =========================================================================== #
# FROM-SCRATCH independent enumerator (Rule I) — raw numpy, shares NO code     #
# =========================================================================== #
# This is a SECOND, independent implementation of the within-cycle (s,f) Bayes floor, written
# from scratch in pure numpy with its own conventions (qutrit 0 = MSB, explicit Kronecker
# embedding, explicit projector matrices). It imports NOTHING from bayes_floor or QutritDM —
# so agreement with the module is certification, not a circular self-check.
def _np_qutrit_ops():
    H = np.zeros((3, 3), complex)
    s = 1.0 / math.sqrt(2.0)
    H[0, 0] = s; H[0, 1] = s; H[1, 0] = s; H[1, 1] = -s; H[2, 2] = 1.0
    X = np.array([[0, 1, 0], [1, 0, 0], [0, 0, 1]], complex)
    Y = np.array([[0, -1j, 0], [1j, 0, 0], [0, 0, 1]], complex)
    Z = np.diag([1.0, -1.0, 1.0]).astype(complex)
    return H, X, Y, Z


def _np_embed(op3, site, n):
    out = np.array([[1.0 + 0j]])
    for j in range(n):
        out = np.kron(out, op3 if j == site else np.eye(3))
    return out


def _np_pauli(kind):
    if kind == "X":
        return np.array([[0, 1, 0], [1, 0, 0], [0, 0, 1]], complex)
    if kind == "Z":
        return np.diag([1.0, -1.0, 1.0]).astype(complex)
    return np.eye(3, complex)


def _np_codestate(stabs, logical, m, n):
    """|m>_L by stabilizer + logical-Z projection of an H-spread seed (independent of the engine)."""
    H, X, Y, Z = _np_qutrit_ops()
    psi = np.zeros(3 ** n, complex); psi[0] = 1.0
    for site in range(n):
        psi = _np_embed(H, site, n) @ psi

    def proj(psi, op, eig):
        opp = psi.copy()
        for site, kind in op.items():
            opp = _np_embed(_np_pauli(kind), site, n) @ opp
        return 0.5 * (psi + float(eig) * opp)

    for g in stabs:
        psi = proj(psi, g, +1)
    psi = proj(psi, logical, (-1) ** m)
    nrm = np.linalg.norm(psi)
    psi = psi / nrm
    return np.outer(psi, psi.conj())


def _np_trit(idx, site, n):
    place = 3 ** (n - 1 - site)
    return (idx // place) % 3


def _np_apply_channel(rho, kraus, site, n):
    out = np.zeros_like(rho)
    for K in kraus:
        E = _np_embed(np.asarray(K, complex), site, n)
        out = out + E @ rho @ E.conj().T
    return 0.5 * (out + out.conj().T)


def _np_project(rho, paulis, outcome, b, n):
    """Diagonal swept-b POVM projector (arm A): rho -> sqrt(E_s) rho sqrt(E_s), UNNORMALIZED."""
    H, X, Y, Z = _np_qutrit_ops()
    x_sites = [s for s, p in paulis.items() if str(p).upper() == "X"]
    for s in x_sites:
        E = _np_embed(H, s, n)
        rho = E @ rho @ E.conj().T
    idx = np.arange(3 ** n)
    d2 = 1.0 - 2.0 * float(b)
    prod = np.ones(3 ** n)
    for site in paulis:
        t = _np_trit(idx, site, n)
        d = np.where(t == 0, 1.0, np.where(t == 1, -1.0, d2))
        prod = prod * d
    sign = 1.0 if (int(outcome) & 1) == 0 else -1.0
    e_diag = 0.5 * (1.0 + sign * prod)
    sq = np.sqrt(np.clip(e_diag, 0.0, None))
    rho = rho * np.outer(sq, sq)
    for s in x_sites:
        E = _np_embed(H, s, n)
        rho = E @ rho @ E.conj().T
    return rho


def _np_logical_sectors(rho, logical, n):
    """(P(L=0), P(L=1)) = tr(Pi_{L=l} rho) on the UNNORMALIZED rho (leaked logical split evenly)."""
    H, X, Y, Z = _np_qutrit_ops()
    x_sites = [s for s, p in logical.items() if str(p).upper() == "X"]
    r = rho.copy()
    for s in x_sites:
        E = _np_embed(H, s, n)
        r = E @ r @ E.conj().T
    diag = np.real(np.diag(r))
    idx = np.arange(3 ** n)
    par = np.zeros(3 ** n, dtype=np.int64)
    leaked = np.zeros(3 ** n, dtype=bool)
    for site in logical:
        t = _np_trit(idx, site, n)
        bit = np.where(t == 2, 0, t)
        par ^= (bit & 1)
        leaked |= (t == 2)
    p0 = float(diag[(par == 0) & (~leaked)].sum() + 0.5 * diag[leaked].sum())
    p1 = float(diag[(par == 1) & (~leaked)].sum() + 0.5 * diag[leaked].sum())
    return p0, p1


def np_enumerate_floor(streams, stabs, logical, leak_np, R, b, n):
    """The INDEPENDENT from-scratch (s,f) Bayes floor by full within-cycle enumeration (numpy)."""
    import itertools

    def history(m):
        rho0 = _np_codestate(stabs, logical, m, n)
        out = {}

        def recurse(rho_in, r, prefix):
            rho = rho_in.copy()
            # pre-M within-cycle stream (H/X gates + exp(L/4) LEAK slices), per qutrit, in order
            H, X, Y, Z = _np_qutrit_ops()
            for q, toks in streams.items():
                for tok in toks:
                    if tok == "LEAK":
                        rho = _np_apply_channel(rho, leak_np, q, n)
                    elif tok == "H":
                        rho = _np_apply_channel(rho, [H], q, n)
                    elif tok == "X":
                        rho = _np_apply_channel(rho, [X], q, n)
            base = rho.copy()
            is_term = (r == R - 1)
            for s in itertools.product((0, 1), repeat=len(stabs)):
                rr = base.copy()
                for k, sk in enumerate(s):
                    rr = _np_project(rr, stabs[k], sk, b, n)
                tr = float(np.real(np.trace(rr)))
                if tr <= 1e-15:
                    continue
                new_prefix = prefix + tuple(int(x) for x in s)
                if is_term:
                    L0, L1 = _np_logical_sectors(rr, logical, n)
                    prev = out.get(new_prefix, (0.0, 0.0))
                    out[new_prefix] = (prev[0] + L0, prev[1] + L1)
                else:
                    rrn = rr / tr
                    # post-M transversal Y on every site
                    for q in range(n):
                        rrn = _np_apply_channel(rrn, [Y], q, n)
                    recurse(rrn * tr, r + 1, new_prefix)

        recurse(rho0, 0, ())
        return out

    h0 = history(0)
    h1 = history(1)
    F = 0.0
    sumps = 0.0
    for s in set(h0) | set(h1):
        a0, a1 = h0.get(s, (0.0, 0.0))
        b0, b1 = h1.get(s, (0.0, 0.0))
        psf0 = 0.5 * (a0 + b1)
        psf1 = 0.5 * (a1 + b0)
        F += min(psf0, psf1)
        sumps += psf0 + psf1
    return F, sumps


# =========================================================================== #
# Shared sub-register problem fixture                                          #
# =========================================================================== #
def _build_problem(R, b=1.0, arm="A", background="leak"):
    """Build the sub-register FloorProblem on the real d3 geometry + the within-cycle leak slice.

    ``background='leak'`` = leak-only (small floor; the cleanest L1 vs the from-scratch enumerator);
    ``background='realistic'`` = the SI1000-style Pauli composed in (larger floor; the regime where
    the L3 bracket + the L2 plug-in down-bias are non-degenerate)."""
    from qec_twin.audit.bayes_floor import FloorProblem
    rgt1 = _load_rgt1()
    sched = xp.parse_xzzx_circuit(_R01_CIRC, _R01_META, verify=True)
    real_streams = {s.pos: tuple(s.tokens) for s in xp.parse_within_cycle_streams(_R10_CIRC, _R10_META)}
    active = sorted(sched.logical)
    loc_streams, stabs_local, logical_local, _info = rgt1.build_subregister(active, real_streams, sched)
    if background == "realistic":
        from p7b_feasibility_profile import combined_slice_np
        leak_np = combined_slice_np(0.07, 0.09, 5e-3, n_cz=3)
    else:
        leak_np = rgt1._leak_slice_np(0.07, 0.09, 0.0, 0.25)
    dev = torch.device("cuda")
    leak_t = [torch.as_tensor(K, dtype=torch.complex128, device=dev) for K in leak_np]
    prob = FloorProblem(n=len(loc_streams), streams={k: list(v) for k, v in loc_streams.items()},
                        stabs=stabs_local, logical=logical_local, leak_kraus=leak_t,
                        b=float(b), arm=str(arm), R=int(R), register_kind="subregister")
    return prob, leak_np, sched, logical_local


# =========================================================================== #
# L1 — mc_floor(R=1) == enumerate_floor(R=1) == the from-scratch enumerator    #
# =========================================================================== #
@requires_cuda
@requires_data
def test_L1_mc_matches_independent_enumeration_R1():
    """L1: ``mc_floor(R=1)`` agrees with ``enumerate_floor(R=1)`` AND with a FROM-SCRATCH numpy
    enumerator (the independent ground truth — Rule I), within 3·MC-SE."""
    from qec_twin.audit.bayes_floor import enumerate_floor, mc_floor
    dev = torch.device("cuda")
    prob, leak_np, _sched, _log = _build_problem(R=1, background="leak")

    # (a) the module's exact enumeration
    en = enumerate_floor(prob, device=dev)
    assert abs(en.meta["sum_Psf"] - 1.0) < 1e-7, en.meta
    # (b) the INDEPENDENT from-scratch enumerator (no shared code)
    F_indep, sumps_indep = np_enumerate_floor(
        prob.streams, prob.stabs, prob.logical, leak_np, prob.R, prob.b, prob.n)
    assert abs(sumps_indep - 1.0) < 1e-7, sumps_indep
    assert abs(en.F_hat - F_indep) < 1e-9, (
        f"module enumerate {en.F_hat} != from-scratch {F_indep} (independent ground-truth fail)")
    # (c) the MC floor agrees within 3 SE
    mc = mc_floor(prob, N=8000, device=dev, seed=11, batch=4000)
    assert mc.F_hat == pytest.approx(F_indep, abs=3.0 * mc.mc_se + 1e-9), (
        f"mc {mc.F_hat} (SE {mc.mc_se}) disagrees with the independent floor {F_indep} by "
        f">3 SE — the exact-per-sample estimator is biased or wired wrong")


@requires_cuda
@requires_data
def test_L1_mc_matches_enumeration_multiround_discriminating():
    """L1 (the DISCRIMINATING regime): ``mc_floor`` (BATCHED evolution) agrees with
    ``enumerate_floor`` (the certified scalar ``QutritDM`` evolution) AND the FROM-SCRATCH
    enumerator at R=2 with the realistic background — a LARGER floor (~1e-2) where the
    floor/SE is small, so a sampling- or observable-bug in the batched MC path WOULD show
    (verified by fault injection: a wrong logical support / branch-sampling flip drives mc→0.5,
    > 3 SE from enumerate). The wider asymmetric sub-register {0,1,2,3} exercises both stabilizer
    types + the multi-round Y/X within-cycle structure."""
    from p7b_feasibility_profile import combined_slice_np
    from qec_twin.audit.bayes_floor import FloorProblem, enumerate_floor, mc_floor
    rgt1 = _load_rgt1()
    dev = torch.device("cuda")
    sched = xp.parse_xzzx_circuit(_R01_CIRC, _R01_META, verify=True)
    real_streams = {s.pos: tuple(s.tokens)
                    for s in xp.parse_within_cycle_streams(_R10_CIRC, _R10_META)}
    loc, sl, ll, _info = rgt1.build_subregister([0, 1, 2, 3], real_streams, sched)
    comb = combined_slice_np(0.07, 0.09, 5e-3, n_cz=3)
    leak_t = [torch.as_tensor(K, dtype=torch.complex128, device=dev) for K in comb]
    prob = FloorProblem(n=len(loc), streams={k: list(v) for k, v in loc.items()}, stabs=sl,
                        logical=ll, leak_kraus=leak_t, b=1.0, arm="A", R=2, register_kind="subregister")
    en = enumerate_floor(prob, device=dev)
    F_indep, sumps = np_enumerate_floor(prob.streams, prob.stabs, prob.logical, comb, prob.R, prob.b, prob.n)
    assert abs(sumps - 1.0) < 1e-7, sumps
    assert abs(en.F_hat - F_indep) < 1e-8, (
        f"module enumerate {en.F_hat} != from-scratch {F_indep} (R=2 realistic ground truth)")
    assert en.F_hat > 5e-3, f"discriminating regime should have a sizeable floor, got {en.F_hat}"
    mc = mc_floor(prob, N=30000, device=dev, seed=3, batch=6000)
    assert mc.F_hat == pytest.approx(F_indep, abs=3.0 * mc.mc_se + 1e-9), (
        f"mc {mc.F_hat} (SE {mc.mc_se}) disagrees with the R=2 enumerate floor {F_indep} by "
        f">3 SE — a batched-evolution / sampling / observable bug")


@requires_cuda
@requires_data
def test_L1_positive_control_broken_observable_trips():
    """L1 positive control: a WRONG observable (the syndrome-only ½(1−TV), observable = m not the
    flip f) gives ≈0.5 — far from the true ~O(leakage) floor. The check that the floor uses the
    FLIP must catch this (else the floor object is wrong)."""
    from qec_twin.audit.bayes_floor import enumerate_floor
    dev = torch.device("cuda")
    prob, _leak_np, _sched, _log = _build_problem(R=1, background="leak")
    F_flip = enumerate_floor(prob, device=dev).F_hat  # the correct (s,f) floor (~5e-4)
    # the WRONG syndrome-only floor: ½(1−TV(P(s|0),P(s|1))) via the engine (observable = m)
    from qec_twin.forward.exact.qutrit_dm import QutritDM

    def synd_dist(m):
        e = QutritDM(prob.n, device=dev)
        e.set_code(stabilizers=prob.stabs, logical_z=prob.logical)
        e.init_logical(m)
        e.apply_within_cycle_premeasure(prob.streams, prob.leak_kraus)
        return e.syndrome_distribution(prob.stabs, b=prob.b, arm=prob.arm, diagonal_z=False)
    p0 = synd_dist(0); p1 = synd_dist(1)
    keys = set(p0) | set(p1)
    tv = 0.5 * sum(abs(p0.get(k, 0.0) - p1.get(k, 0.0)) for k in keys)
    F_wrong = 0.5 * (1.0 - tv)
    assert F_wrong > 0.4, f"syndrome-only floor expected ~0.5, got {F_wrong}"
    assert F_flip < 1e-2, f"flip-aligned floor expected O(leakage), got {F_flip}"
    # the control: the two objects are wildly different (the observable choice is load-bearing)
    assert F_wrong - F_flip > 0.4, (
        "the wrong (syndrome-only) and correct (flip-aligned) floors must differ by ~0.5 — "
        "if they coincided the observable-alignment check would be inert")


# =========================================================================== #
# L2 — convergence / no-drift tripwire (+ the positive control that fires)     #
# =========================================================================== #
@requires_cuda
@requires_data
def test_L2_convergence_mc_flat_plugin_rises():
    """L2: ``mc_floor`` does NOT drift with N (slope ≈ 0 within SE); the in-sample PLUG-IN RISES
    with N (slope > 0 — the positive control that the down-bias tripwire fires)."""
    from qec_twin.audit.bayes_floor import floor_convergence_report
    dev = torch.device("cuda")
    # the realistic-background regime: enough record collisions that the plug-in's RISE is visible
    prob, _leak_np, _sched, _log = _build_problem(R=3, background="realistic")
    rep = floor_convergence_report(prob, device=dev, N_sweep=(2000, 8000, 32000), seed=3, batch=4000)
    # mc is flat within SE (unbiased)
    assert rep["mc_flat"], (
        f"mc_floor drifted with N (slope {rep['mc_slope_per_decade']:.2e} per decade, "
        f"SE {rep['mc_slope_se']:.2e}) — an unbiased estimator must be flat")
    # the positive control: the plug-in RISES with N (the down-bias signature the spec predicts)
    assert rep["plugin_rises"], (
        f"plug-in did NOT rise with N (slope {rep['plugin_slope_per_decade']:.2e}) — the "
        f"down-bias tripwire's positive control did not fire; the plug-in must rise in the "
        f"under-sampled regime (FAITHFULNESS_PROTOCOL ledger 7)")
    # and the rise is genuinely larger than the (flat) mc drift
    assert rep["plugin_slope_per_decade"] > abs(rep["mc_slope_per_decade"]), (
        "the plug-in's upward drift must exceed the mc estimator's (flat) drift")


# =========================================================================== #
# L3 — plugin <= mc <= crossfit within SE (MC inside the valid bracket)        #
# =========================================================================== #
@requires_cuda
@requires_data
def test_L3_mc_inside_plugin_crossfit_bracket():
    """L3: ``E[plugin] ≤ F ≤ E[crossfit]`` and the MC estimate lands inside ``[plugin, crossfit]``
    within SE (spec §1 — the sample-splitting identity)."""
    from qec_twin.audit.bayes_floor import (
        crossfit_floor, enumerate_floor, mc_floor, plugin_floor, sample_teacher_records)
    dev = torch.device("cuda")
    prob, _leak_np, _sched, _log = _build_problem(R=3, background="realistic")
    F_exact = enumerate_floor(prob, device=dev).F_hat
    det, flip = sample_teacher_records(prob, N=200000, device=dev, seed=5, batch=20000)
    pl = plugin_floor(det, flip)
    cf = crossfit_floor(det, flip, seed=7)
    mc = mc_floor(prob, N=20000, device=dev, seed=9, batch=4000)
    tol_lo = mc.mc_se + pl.mc_se + 1e-9
    tol_hi = mc.mc_se + cf.mc_se + 1e-9
    assert pl.F_hat <= mc.F_hat + tol_lo, f"plugin {pl.F_hat} > mc {mc.F_hat} (+{tol_lo:.1e})"
    assert mc.F_hat <= cf.F_hat + tol_hi, f"mc {mc.F_hat} > crossfit {cf.F_hat} (+{tol_hi:.1e})"
    # the bracket brackets the EXACT floor (the identity's point)
    assert pl.F_hat <= F_exact + pl.mc_se + 1e-9, f"plugin {pl.F_hat} above exact F {F_exact}"
    assert F_exact <= cf.F_hat + cf.mc_se + 1e-9, f"exact F {F_exact} above crossfit {cf.F_hat}"


@requires_cuda
@requires_data
def test_L3_positive_control_plugin_below_crossfit():
    """L3 positive control: in the under-sampled regime the plug-in is STRICTLY below the cross-fit
    (the bracket has positive width) — if they coincided the bracket would be inert. We force the
    under-sampled regime with a small N where collisions are rare."""
    from qec_twin.audit.bayes_floor import bracket_floor, sample_teacher_records
    dev = torch.device("cuda")
    prob, _leak_np, _sched, _log = _build_problem(R=3, background="realistic")
    det, flip = sample_teacher_records(prob, N=6000, device=dev, seed=21, batch=3000)
    pl, cf = bracket_floor(det, flip, seed=3)
    assert cf >= pl - 1e-12, f"cross-fit {cf} < plug-in {pl} (bracket inverted)"
    assert cf - pl > 1e-4, (
        f"bracket width {cf - pl:.2e} ~0 — the [plugin, crossfit] bracket is inert in this "
        f"under-sampled regime (the down-bias/up-bias separation must be visible)")


# =========================================================================== #
# L6 — probability sanity along paths                                          #
# =========================================================================== #
@requires_cuda
@requires_data
def test_L6_probability_sanity():
    """L6: ``0 ≤ P(s,f)``; ``P(s,0)+P(s,1)=P(s)``; sampled ``Σ P(s)=1``; CPTP / trace residual
    < 1e-9 along every path (the per-pass sanity the mc_floor records)."""
    from qec_twin.audit.bayes_floor import enumerate_floor, mc_floor
    dev = torch.device("cuda")
    prob, _leak_np, _sched, _log = _build_problem(R=2, background="realistic")
    mc = mc_floor(prob, N=8000, device=dev, seed=4, batch=4000, sanity=True)
    assert mc.meta["sanity_neg_residual"] < 1e-12, mc.meta            # 0 <= P(s,f)
    assert mc.meta["sanity_norm_residual"] < 1e-9, mc.meta            # P(s,0)+P(s,1)=P(s)
    assert mc.meta["sanity_trace_residual"] < 1e-9, mc.meta           # per-path trace conservation
    assert mc.meta["cptp_residual"] < 1e-9, mc.meta                   # the leak slice is CPTP
    # enumerate gives an exact normalized (s,f) joint: Σ P(s) = 1
    en = enumerate_floor(prob, device=dev)
    assert abs(en.meta["sum_Psf"] - 1.0) < 1e-7, en.meta
    assert abs(en.meta["sum_P0"] - 1.0) < 1e-7 and abs(en.meta["sum_P1"] - 1.0) < 1e-7, en.meta


@requires_cuda
@requires_data
def test_L6_positive_control_cptp_residual_trips_on_broken_kraus():
    """L6 positive control: a NON-CPTP leak slice (Kraus scaled so ΣK†K ≠ I) must be CAUGHT by the
    explicit CPTP residual.

    NOTE the subtlety (why the CPTP gate is the explicit Kraus residual, not the floor value): the
    floor ``min(P(s,0),P(s,1))/P(s)`` is a CONDITIONAL ratio, so a UNIFORM Kraus rescale cancels in
    the ratio and is invisible to the floor itself (a robustness feature). The faithful CPTP check
    is therefore on the channel directly — ``cptp_residual(K)`` — which we assert here BOTH fires on
    the broken slice AND is ~0 on the faithful one (a check that cannot fail is not a check)."""
    from qec_twin.audit.bayes_floor import cptp_residual
    dev = torch.device("cuda")
    prob, leak_np, _sched, _log = _build_problem(R=2, background="leak")
    faithful = [torch.as_tensor(K, dtype=torch.complex128, device=dev) for K in leak_np]
    # deliberately break CPTP: scale every Kraus by 1.3 (ΣK†K = 1.69·I, not I)
    broken = [1.3 * K for K in faithful]
    resid_ok = cptp_residual(faithful)
    resid_bad = cptp_residual(broken)
    assert resid_ok < 1e-9, f"faithful leak slice CPTP residual {resid_ok} should be ~0"
    assert resid_bad > 1e-2, (
        f"non-CPTP leak slice (×1.3) CPTP residual {resid_bad} did NOT trip — the CPTP check is "
        f"inert (a broken channel must be caught)")


# =========================================================================== #
# Observable alignment (the L5 hook OWNED here): the floor's logical projector  #
# matches the teacher's logical observable m                                    #
# =========================================================================== #
@requires_cuda
@requires_data
def test_observable_projector_matches_teacher_logical_m():
    """The floor's logical PROJECTOR (used to read the flip f) reads the teacher's logical
    observable m EXACTLY: on |m>_L (no noise, no syndrome projection) the logical-sector trace is a
    clean (1,0)/(0,1) selecting m (the projector IS the teacher's logical Z on {0,2,5})."""
    from qec_twin.audit.bayes_floor import _logical_sector_traces_batched
    from qec_twin.forward.exact.qutrit_dm import QutritDM
    dev = torch.device("cuda")
    prob, _leak_np, sched, logical_local = _build_problem(R=1, background="leak")
    # the floor uses prob.logical; assert it is exactly the schedule's logical observable restricted
    # to the active register (the teacher's m), NOT some other operator.
    active = sorted(sched.logical)
    site_to_local = {s: i for i, s in enumerate(active)}
    real_restricted = {site_to_local[q]: k for q, k in sched.logical.items() if q in set(active)}
    # the sub-register builder may FORCE a local logical when the restriction is empty; here the
    # logical support {0,2,5} == the active set, so the restriction is non-empty and must match.
    assert real_restricted, "the real logical restricted to the active set is empty (unexpected)"
    assert prob.logical == real_restricted, (
        f"floor logical {prob.logical} != teacher logical restricted {real_restricted} — the "
        f"floor would score the WRONG observable")
    # and the projector reads m cleanly on |m>_L
    for m in (0, 1):
        e = QutritDM(prob.n, device=dev)
        e.set_code(stabilizers=prob.stabs, logical_z=prob.logical)
        e.init_logical(m)
        L0, L1 = _logical_sector_traces_batched(e.rho.unsqueeze(0), prob.logical, prob.n, dev)
        L0, L1 = float(L0.item()), float(L1.item())
        # |m>_L is a logical-Z eigenstate with eigenvalue (-1)^m → all mass in sector m
        if m == 0:
            assert L0 == pytest.approx(1.0, abs=1e-9) and L1 == pytest.approx(0.0, abs=1e-9), (L0, L1)
        else:
            assert L1 == pytest.approx(1.0, abs=1e-9) and L0 == pytest.approx(0.0, abs=1e-9), (L0, L1)

"""Stage-D batch ``groundtruth_nulls`` -- per-unit L0+L1 coverage of the two
anti-toy oracle modules of ``error_coupling_simulator.quantum_bath``:

  * ``ground_truth.py`` (6 units): the Rule-I INDEPENDENT reference computations --
    each scores the shared-bath carrier against a closed form / exact ODE / full
    Liouvillian derived WITHOUT the carrier construction.
  * ``nulls.py`` (6 units): the MATCHED incoherent-AD null family + the model-free
    record-distance (min-TV) discriminator.

Both modules are CPU-pure (numpy / scipy.linalg.expm / math; NO torch, NO quimb), so
they get the FULL treatment: L0 (100% statement + BOTH arcs of every tracked branch per
unit) + L1 (Hypothesis faithfulness properties for the batch invariants). L2 (mutmut)
runs in Stage E. Everything is in scope -- there is no out_of_scope park.

NB on the "branch surface" (coverage.py --branch). coverage.py emits NO tracked branch
arc for a pure generator/comprehension body, so a unit whose ONLY compound statement is
a dict/generator comprehension scores branch 0/0 (nothing to miss) -- that is honest, not
a hole; its faithfulness rests on the L1 PROPERTY. Concretely ``no_bath_sanity`` (its P1
marginal is a dict-comprehension) and ``full_superop_bytes`` / ``factorization_check``
(straight-line, no compound stmt) score 0/0 branch. The real branch teeth live in the
units that carry ``if``/``for``/ternary decisions:

  MODULE.UNIT                       L0 branch surface (both arcs covered)   L1 faithfulness property
  -----------                       ------------------------------------    ------------------------
  gt.full_superop_bytes             none tracked (straight-line; 0/0)       D^2*D^2*16 bytes, monotone in nmax
  gt.factorization_check            none tracked (straight-line; 0/0)       max_abs_err -> 0 (reduced == full L)
  gt.extraction_gt_check            2 for-loops (both iterate)              worst_err_X/Z -> 0 (deterministic parity)
  gt.two_qubit_indep_boson_gt       nested row/col for-loops               worst_err -> 0 (indep-boson closed form)
  gt.sigma_minus_emission_gt        for it in range (both arcs)            worst_err -> 0 (GKSL == amplitude ODE)
  gt.no_bath_sanity                 comprehension body (0/0)               K/CMI/M_mem ~ 0 (bath off => Markov-0)
  nulls.axis_ad_null_point          if flip-None + 3 ternaries + fors      CPTP: P_all>=0, sum==1; K>=0
  nulls.coherent_ad_null_point      if flip-None + fors                    CPTP: P_all>=0, sum==1; K>=0
  nulls.min_tv_to_incoherent        2 if tv<best + nm for-loop (both)      TV in [0,1]
  nulls.classical_ad_null_point     nested for-loops                       CPTP: P_all>=0, sum==1; K>=0
  nulls.classical_nonmarkov_ad_...  nested for-loops                       CPTP: P_all>=0, sum==1; K>=0, CMI>=0
  nulls.collective_ad_null_point    nested for-loops                       CPTP: P_all>=0, sum==1; K>=0

BRANCH-COVERAGE NOTES (the load-bearing per-unit L0 requirements):
  * ``axis_ad_null_point`` / ``coherent_ad_null_point`` carry an ``if flip is None: ...
    else: ...`` decision -- BOTH the Markovian (flip=None) and the non-Markovian
    (flip=<value>) arcs are exercised. ``axis_ad_null_point`` ALSO has three
    ``x = default if x is None else x`` ternaries (p1/theta1/phi1): one call leaves them
    None (default/collective arc), one passes all three (explicit/biaxial arc).
  * ``min_tv_to_incoherent`` carries ``if tv < best[0]`` inside BOTH the grid loop and the
    non-Markovian loop, plus the ``for ... in nm_list`` loop. The nm loop's not-entered arc
    is exercised by an empty ``nm_list`` (default); its entered arc + the ``if tv<best``
    True/False arcs by a non-empty ``nm_list`` where an exact match improves and a decoy
    does not.

NON-NEGATIVITY TOLERANCE (faithfulness detail). The null P_all entries are traces of
positive branches, non-negative UP TO floating-point noise: ``collective_ad_null_point``
produces min entries ~ -1e-17 (an expm/kron round-off, not a real negative probability).
The CPTP L1 property therefore asserts ``min(P_all) >= -1e-12`` (the package NUMERICAL_ZERO
floor), not ``>= 0`` exactly -- a structural-negative would be a genuine bug and still bites.

KILLER teeth (Side-A). Four load-bearing asserts are each shown DISCRIMINATING with an
inlined sabotaged variant that VIOLATES the property in the claimed direction (verified):
  * drop the AD jump Kraus E1 (non-trace-preserving) => record norm 0.45 < 1 (CPTP sum==1);
  * drop abs() in K with an over-normalized skip => signed K = -1 < 0 (K>=0);
  * flip the sign of the independent-boson exponent => GT worst_err 0.05 (worst_err->0);
  * drop the 0.5 factor in TV => 1.41 > 1 (TV in [0,1]).
"""
from __future__ import annotations

import math
import os

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from error_coupling_simulator.numerics import NUMERICAL_ZERO
from error_coupling_simulator.quantum_bath import ground_truth as gt
from error_coupling_simulator.quantum_bath import nulls
from error_coupling_simulator.quantum_bath.carrier import (
    _extract_x_full,
    _extract_z_full,
    _initial_rho_dual,
    _on_qubit4,
    dual_extract,
)
from error_coupling_simulator.quantum_bath.crow_joynt import gamma_unit_closed
from error_coupling_simulator.quantum_bath.gksl import round_superop
from error_coupling_simulator.quantum_bath.observables import (
    K_stat_binary,
    K_stat_joint,
    M_ALPHABET,
    project_axis,
    tv_distance,
)

# GT closed forms match to ~1e-16; nulls norms to ~1e-13 (accumulated round-off over 8
# latent trajectories x 3 rounds). These floors are the L1 tolerances.
_GT_EXACT = 1e-9          # a *_gt worst_err below this is "recovers the closed form"
_NORM_TOL = 1e-8          # sum(P_all) == 1 up to this
_NN_TOL = NUMERICAL_ZERO  # P_all entries >= -NUMERICAL_ZERO (float round-off floor)


# --------------------------------------------------------------------------- #
# shared helpers (deterministic; the batch's fixtures, not ad-hoc harness)     #
# --------------------------------------------------------------------------- #
def _cptp_ok(res: dict, *, expect_cmi_nonneg: bool = True) -> None:
    """Assert a null-point result is a bona-fide record distribution: non-negative
    P_all (up to the round-off floor), total mass 1, K statistics >= 0, and (when the
    null carries genuine 3-round memory) CMI >= 0. These are the L1 invariants for every
    ``*_null_point`` unit.

    NB (reviewer 2026-07-07, MEDIUM): these are CPTP-INVARIANTS ONLY -- an identity or a
    fixed random-unitary channel (both CPTP through the instrument) passes every one of
    them (K = sum-of-|.| >= 0 always; sum(P)==1 for any trace-preserving map). They are
    NECESSARY but NON-DISCRIMINATING. The per-unit tests therefore ADD a discriminating
    pin (a K value, a record entry, or the incoherence signature K_X ~ 0) verified against
    an INDEPENDENT recompute -- see the ``_indep_*`` reference and the per-test asserts.
    A vacuous-only ``_cptp_ok`` was the finding; it is retained as the CPTP floor, not the
    faithfulness test."""
    P = res["P_all"]
    assert min(P.values()) >= -_NN_TOL, f"negative probability {min(P.values())}"
    assert abs(sum(P.values()) - 1.0) < _NORM_TOL, f"unnormalized: {sum(P.values())}"
    assert res["norm"] == pytest.approx(sum(P.values()))
    for key in ("K_joint", "K_X", "K_Z"):
        assert res[key] >= -1e-12, f"{key} negative: {res[key]}"
    assert res["M_mem"] >= 0.0
    if expect_cmi_nonneg:
        assert res["CMI"] >= -1e-9, f"CMI negative: {res['CMI']}"


# --------------------------------------------------------------------------- #
# INDEPENDENT from-scratch reference (Rule I): a 2-DATA-QUBIT-ONLY (4-dim)      #
# reimplementation of the incoherent-AD dual-axis null. It shares NO code with  #
# nulls.py / carrier.py: explicit AD Kraus + explicit XX/ZZ parity projectors   #
# (NOT ancilla-mediated extraction), no shared mode, no ``_ad_channel_*`` /      #
# ``_axis_ad_kraus`` / ``dual_extract`` / ``K_stat_*`` imports. It reproduces    #
# the module's K_Z / K_X / record entries to machine precision (verified), so a  #
# pin against it is a genuine non-circular discriminator: an identity channel    #
# gives K_Z=0 (no AD memory), any coherent/random-unitary channel gives K_X != 0 #
# (spurious complementary-axis imprint).                                         #
# --------------------------------------------------------------------------- #
_I2 = np.eye(2, dtype=complex)
_PX = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
_PZ = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
_ALPHA4 = [(0, 0), (0, 1), (1, 0), (1, 1)]
_PLUS = np.array([1.0, 1.0], dtype=complex) / math.sqrt(2.0)
_RHO0_2Q = np.outer(np.kron(_PLUS, _PLUS), np.kron(_PLUS, _PLUS).conj())
_XX = np.kron(_PX, _PX)
_ZZ = np.kron(_PZ, _PZ)
_PROJ_X = {0: 0.5 * (np.eye(4, dtype=complex) + _XX), 1: 0.5 * (np.eye(4, dtype=complex) - _XX)}
_PROJ_Z = {0: 0.5 * (np.eye(4, dtype=complex) + _ZZ), 1: 0.5 * (np.eye(4, dtype=complex) - _ZZ)}


def _indep_ad_both(rho, p):
    """Incoherent AD (prob p, toward Z) on both data qubits -- from-scratch Kraus, 4-dim."""
    s, rr = math.sqrt(1.0 - p), math.sqrt(p)
    ks = [np.array([[1.0, 0.0], [0.0, s]], dtype=complex),
          np.array([[0.0, rr], [0.0, 0.0]], dtype=complex)]
    out = np.zeros_like(rho)
    for E in ks:
        Eq = np.kron(E, _I2)
        out = out + Eq @ rho @ Eq.conj().T
    out2 = np.zeros_like(rho)
    for E in ks:
        Eq = np.kron(_I2, E)
        out2 = out2 + Eq @ out @ Eq.conj().T
    return out2


def _indep_dual_measure(rho):
    """X-parity then Z-parity projective instrument (commuting), 4-dim; keep all 4 branches."""
    out = {}
    for sX in (0, 1):
        bx = _PROJ_X[sX] @ rho @ _PROJ_X[sX]
        for sZ in (0, 1):
            out[(sX, sZ)] = _PROJ_Z[sZ] @ bx @ _PROJ_Z[sZ]
    return out


def _indep_proj_axis(P, which):
    out: dict = {}
    for k, v in P.items():
        nk = tuple(m[which] for m in k)
        out[nk] = out.get(nk, 0.0) + v
    return out


def _indep_Kbin(Pa, Ps):
    return float(sum(abs(sum(Pa[(s1, s2, s3)] for s2 in (0, 1)) - Ps[(s1, s3)])
                     for s1 in (0, 1) for s3 in (0, 1)))


def _indep_records(p_of_round):
    """Exact 3-round (P_all, P_skip) for AD probs (p1,p2,p3) applied per round -- from-scratch."""
    p1, p2, p3 = p_of_round
    P_all, P_skip = {}, {}
    r1 = _indep_ad_both(_RHO0_2Q, p1); b1 = _indep_dual_measure(r1)
    for m1 in _ALPHA4:
        a1 = b1[m1]; r2 = _indep_ad_both(a1, p2); b2 = _indep_dual_measure(r2)
        for m2 in _ALPHA4:
            a2 = b2[m2]; r3 = _indep_ad_both(a2, p3); b3 = _indep_dual_measure(r3)
            for m3 in _ALPHA4:
                P_all[(m1, m2, m3)] = float(np.trace(b3[m3]).real)
        r_ev = _indep_ad_both(_indep_ad_both(a1, p2), p3); bs = _indep_dual_measure(r_ev)
        for m3 in _ALPHA4:
            P_skip[(m1, m3)] = float(np.trace(bs[m3]).real)
    return P_all, P_skip


def _indep_markov_KZ_KX(p):
    """Independent (K_Z, K_X, P000) for a Markovian AD-toward-Z null at prob p."""
    Pa, Ps = _indep_records((p, p, p))
    KZ = _indep_Kbin(_indep_proj_axis(Pa, 1), _indep_proj_axis(Ps, 1))
    KX = _indep_Kbin(_indep_proj_axis(Pa, 0), _indep_proj_axis(Ps, 0))
    return KZ, KX, Pa[((0, 0), (0, 0), (0, 0))]


def _indep_nonmarkov_KZ_KX(flip, p_lo, p_hi):
    """Independent (K_Z, K_X) for the 2-state-latent-modulated AD-toward-Z null."""
    T = np.array([[1.0 - flip, flip], [flip, 1.0 - flip]], dtype=float)
    pi = np.array([0.5, 0.5], dtype=float)
    p_of = {0: p_lo, 1: p_hi}
    P_all = {(m1, m2, m3): 0.0 for m1 in _ALPHA4 for m2 in _ALPHA4 for m3 in _ALPHA4}
    P_skip = {(m1, m3): 0.0 for m1 in _ALPHA4 for m3 in _ALPHA4}
    for x1 in (0, 1):
        for x2 in (0, 1):
            for x3 in (0, 1):
                w = pi[x1] * T[x1, x2] * T[x2, x3]
                pa, ps = _indep_records((p_of[x1], p_of[x2], p_of[x3]))
                for k in P_all:
                    P_all[k] += w * pa[k]
                for k in P_skip:
                    P_skip[k] += w * ps[k]
    KZ = _indep_Kbin(_indep_proj_axis(P_all, 1), _indep_proj_axis(P_skip, 1))
    KX = _indep_Kbin(_indep_proj_axis(P_all, 0), _indep_proj_axis(P_skip, 0))
    return KZ, KX


# =========================================================================== #
# L0 -- ground_truth.py : per-unit statement + branch coverage                 #
# =========================================================================== #
def test_L0_full_superop_bytes():
    # straight-line arithmetic (no branch): D=(16*nmax), returns D^2 * D^2 * 16 bytes.
    assert gt.full_superop_bytes(1) == pytest.approx((16 ** 2) ** 2 * 16)
    assert gt.full_superop_bytes(2) == pytest.approx((32 ** 2) ** 2 * 16)
    # monotone in nmax (a bigger mode Hilbert space => a bigger superop)
    assert gt.full_superop_bytes(3) > gt.full_superop_bytes(2) > gt.full_superop_bytes(1)


def test_L0_factorization_check_runs_and_matches_full_liouvillian():
    # small nmax keeps the full 16*nmax Liouvillian cheap; the reduced apply must equal it.
    r = gt.factorization_check(nmax=2, zeta=1.0, gamma=0.3, g0z=0.2, g1z=0.15,
                               g0m=0.1, g1m=0.05, tau=0.7)
    assert r["nmax"] == 2
    assert r["max_abs_err"] < _GT_EXACT          # reduced (E_red x I x I) == full L
    assert r["full_superop_GB"] == pytest.approx(gt.full_superop_bytes(2) / 1e9)


def test_L0_extraction_gt_check_deterministic_parity():
    # both for-loops iterate (4 X-parity eigenstates + 4 Z-parity eigenstates); each
    # ancilla reads its parity deterministically -> worst_err ~ 0 on both axes.
    r = gt.extraction_gt_check()
    assert r["worst_err_X"] < _GT_EXACT
    assert r["worst_err_Z"] < _GT_EXACT


def test_L0_two_qubit_indep_boson_gt_matches_closed_form():
    # nested row/col for-loops over the 4x4 reduced (d0,d1) coherence block; each entry
    # vs 0.25 exp(-(ds)^2 Gamma_unit). Small nmax (=6) keeps it fast; coverage is
    # nmax-independent (same code path).
    r = gt.two_qubit_indep_boson_gt(nmax=6, zeta=1.0, gamma=0.3, g0z=0.2, g1z=0.15, tau=0.7)
    assert r["worst_err"] < _GT_EXACT
    assert r["Gamma_unit_tau"] == pytest.approx(gamma_unit_closed(0.7, 1.0, 0.3))


def test_L0_sigma_minus_emission_gt_matches_amplitude_ode():
    # for it in range(1, n_t+1): both arcs (enter + exit). p_e(t) from the GKSL == the
    # exact single-excitation amplitude ODE at every sampled t.
    r = gt.sigma_minus_emission_gt(nmax=5, zeta=1.0, gamma=0.3, g=0.2, tau=1.0, n_t=4)
    assert r["worst_err"] < _GT_EXACT
    assert len(r["series"]) == 4
    assert 0.0 <= r["pe_final_gksl"] <= 1.0
    # default n_t path (=6) also runs
    r6 = gt.sigma_minus_emission_gt(nmax=5, zeta=1.0, gamma=0.3, g=0.2, tau=1.0)
    assert len(r6["series"]) == 6


def test_L0_no_bath_sanity_flat_markov0():
    # bath off (gamma=0, all couplings 0) -> flat Markov-0 record: K/CMI/M_mem all ~ 0.
    # (P1 marginal is a dict-comprehension -> branch 0/0, tracked as nothing to miss.)
    r = gt.no_bath_sanity(2)
    assert abs(r["K_joint"]) < 1e-9 and abs(r["K_X"]) < 1e-9 and abs(r["K_Z"]) < 1e-9
    assert abs(r["CMI"]) < 1e-9 and abs(r["M_mem"]) < 1e-9
    assert 0.0 <= r["p_max_marginal"] <= 1.0


# =========================================================================== #
# L0 -- nulls.py : per-unit statement + branch coverage                        #
# =========================================================================== #
def test_L0_axis_ad_null_point_markovian_default_axis():
    # flip=None -> the Markovian arc of `if flip is None`; p1/theta1/phi1 left None ->
    # the DEFAULT (collective) arc of the three `x = p0 if x is None else x` ternaries.
    r = nulls.axis_ad_null_point(p0=0.2, theta0=0.3, phi0=0.4)
    _cptp_ok(r, expect_cmi_nonneg=True)
    # DISCRIMINATING (finding MEDIUM): pin the AD-toward-PURE-Z null (theta0=0) K_Z to an
    # INDEPENDENT recompute + assert its incoherence signature K_X ~ 0. Identity -> K_Z=0
    # (no AD memory) fails the K_Z pin; a random-unitary/coherent channel -> K_X != 0 fails
    # the K_X pin. Together they force the Markovian AD-toward-Z PHYSICS, not just CPTP.
    rz = nulls.axis_ad_null_point(p0=0.3, theta0=0.0, phi0=0.0)
    KZ_ind, KX_ind, _ = _indep_markov_KZ_KX(0.3)
    assert KZ_ind > 0.1                                    # the reference is a real nonzero
    assert rz["K_Z"] == pytest.approx(KZ_ind, abs=1e-12)   # pin K_Z vs independent recompute
    assert rz["K_X"] < 1e-9                                # incoherence: no complementary imprint
    # the DEFAULT-ternary (collective) arc has BOTH data qubits on the same axis/prob, so its
    # X-marginal K is also tiny (theta0=0.3 tilts it a hair but stays << a coherent null's ~0.24)
    assert r["K_X"] < 1e-2 < 0.2


def test_L0_axis_ad_null_point_nonmarkovian_biaxial():
    # flip=<value> -> the NON-Markovian (8-trajectory) arc of `if flip is None`; passing
    # all of p1/theta1/phi1 -> the EXPLICIT arc of the three ternaries (biaxial per-qubit).
    r = nulls.axis_ad_null_point(p0=0.2, theta0=0.3, phi0=0.4,
                                 p1=0.15, theta1=0.5, phi1=0.6,
                                 flip=0.2, p_lo=0.5, p_hi=1.5)
    _cptp_ok(r, expect_cmi_nonneg=True)
    # DISCRIMINATING: the non-Markovian arc must carry GENUINE 3-round memory (a Markovian
    # mutant -- e.g. one that ignores `flip` and takes the single-trajectory branch, or
    # collapses the latent weights -- gives CMI ~ 0, M_mem ~ 0). Pin both strictly positive
    # AND pin K_joint to the exact value (catches a mutant that mis-weights the trajectories).
    assert r["CMI"] == pytest.approx(0.000300835082766, abs=1e-12)   # genuine non-Markov CMI
    assert r["M_mem"] == pytest.approx(0.008799095209286, abs=1e-12)
    assert r["K_joint"] == pytest.approx(0.044329255073818, abs=1e-12)
    assert r["P_all"][((0, 0), (0, 0), (0, 0))] == pytest.approx(0.344987730841298, abs=1e-12)


def test_L0_coherent_ad_null_point_markovian_and_nonmarkovian():
    # `if flip is None` both arcs: Markovian (flip=None) then non-Markovian (flip=0.2).
    m = nulls.coherent_ad_null_point(u0=(0.1, 0.2, 0.3), u1=(0.2, 0.1, 0.4),
                                     ad0=(0.2, 0.3, 0.4), ad1=(0.15, 0.5, 0.6), zz=0.3)
    _cptp_ok(m, expect_cmi_nonneg=True)
    # DISCRIMINATING: this null CARRIES coherence (the per-qubit unitaries + ZZ). Its
    # complementary-axis imprint K_X is LARGE and specific. A mutant that drops the coherent
    # unitary step (Ucoh) collapses to an incoherent-AD record with K_X ~ 0, so pinning K_X
    # to its exact large value bites. K_joint pin catches any channel-composition mutation.
    assert m["K_X"] == pytest.approx(0.237284358806705, abs=1e-9)   # coherence signature (large)
    assert m["K_X"] > 0.2                                            # >> the incoherent nulls' ~0
    assert m["K_joint"] == pytest.approx(0.276472450195, abs=1e-9)
    nm = nulls.coherent_ad_null_point(u0=(0.1, 0.2, 0.3), u1=(0.2, 0.1, 0.4),
                                      ad0=(0.2, 0.3, 0.4), ad1=(0.15, 0.5, 0.6), zz=0.3,
                                      flip=0.2, p_lo=0.5, p_hi=1.5)
    _cptp_ok(nm, expect_cmi_nonneg=True)
    # the non-Markovian arc: coherence (K_X large) AND genuine memory (CMI > 0).
    assert nm["K_X"] == pytest.approx(0.241257036295385, abs=1e-9)
    assert nm["CMI"] == pytest.approx(0.000247586442562, abs=1e-12)  # latent memory present


def test_L0_classical_ad_null_point():
    r = nulls.classical_ad_null_point(p=0.25)
    _cptp_ok(r, expect_cmi_nonneg=True)
    assert r["p"] == 0.25
    # DISCRIMINATING (finding MEDIUM): pin K_Z + a record entry against the INDEPENDENT
    # from-scratch (2-qubit, parity-projector) recompute, and K_X ~ 0 (incoherence). An
    # identity channel gives K_Z=0 (fails); a random-unitary/coherent channel gives K_X != 0
    # (fails); a mutant that mis-applies the AD prob (e.g. p->1-p, or a single-qubit instead
    # of both) shifts K_Z / P000 off the independent value (fails).
    KZ_ind, KX_ind, P000_ind = _indep_markov_KZ_KX(0.25)
    assert KZ_ind == pytest.approx(0.09375, abs=1e-12)             # independent closed value
    assert r["K_Z"] == pytest.approx(KZ_ind, abs=1e-12)            # pin vs independent recompute
    assert r["K_X"] < 1e-9                                         # incoherence signature
    assert r["P_all"][((0, 0), (0, 0), (0, 0))] == pytest.approx(P000_ind, abs=1e-12)
    assert P000_ind == pytest.approx(0.276565551757812, abs=1e-12)


def test_L0_classical_nonmarkov_ad_null_point():
    # the 8-trajectory latent-modulated AD: carries genuine 3-round memory (CMI, M_mem > 0)
    # but is INCOHERENT (K_X ~ 0). Non-negative + normalized + K>=0 + CMI>=0 all hold.
    r = nulls.classical_nonmarkov_ad_null_point(flip=0.2, p_lo=0.1, p_hi=0.4)
    _cptp_ok(r, expect_cmi_nonneg=True)
    assert r["flip"] == 0.2 and r["p_lo"] == 0.1 and r["p_hi"] == 0.4
    # DISCRIMINATING (finding MEDIUM): pin K_Z vs the INDEPENDENT 2-state-latent recompute;
    # the incoherence signature K_X ~ 0; and CMI/M_mem STRICTLY positive (the classical
    # latent memory the quantum record must exceed). A mutant that ignores the latent
    # (Markovian collapse) -> CMI ~ 0 (fails); an identity -> K_Z=0 (fails); a coherent
    # mutant -> K_X != 0 (fails).
    KZ_ind, KX_ind = _indep_nonmarkov_KZ_KX(0.2, 0.1, 0.4)
    assert KZ_ind == pytest.approx(0.096, abs=1e-12)
    assert r["K_Z"] == pytest.approx(KZ_ind, abs=1e-12)           # pin vs independent recompute
    assert r["K_X"] < 1e-9                                        # incoherent (no coherence gen)
    assert r["CMI"] == pytest.approx(0.001607490183685, abs=1e-12)   # genuine classical memory
    assert r["M_mem"] > 1e-3


def test_L0_collective_ad_null_point():
    # the Dicke collective jump. min entry ~ -1e-17 (expm/kron round-off) so the CPTP
    # helper uses the NUMERICAL_ZERO floor, not exact >= 0.
    r = nulls.collective_ad_null_point(gamma_c=0.3, tau=0.7)
    _cptp_ok(r, expect_cmi_nonneg=True)
    assert r["gamma_c"] == 0.3
    # DISCRIMINATING: the Dicke COLLECTIVE jump c = sqrt(gamma_c)(sm_d0 + sm_d1) has a
    # CROSS term (~sqrt(J1 J2)) that per-qubit independent AD lacks -> a specific nonzero
    # K_X (unlike the independent-AD nulls whose K_X ~ 0). Pin K_joint + K_X to their exact
    # values. An identity (gamma_c/tau ignored) -> all K = 0 (fails K_joint); a mutant that
    # drops the cross term / uses a single-qubit jump shifts K_X off (fails).
    assert r["K_joint"] == pytest.approx(0.071700438823720, abs=1e-9)
    assert r["K_X"] == pytest.approx(0.035850219411859, abs=1e-9)  # collective cross-term imprint
    assert r["K_X"] > 1e-2                                          # NOT the incoherent K_X~0
    # a zero-strength collective channel (gamma_c=0) is the identity -> flat record, K=0:
    r0 = nulls.collective_ad_null_point(gamma_c=0.0, tau=0.7)
    assert r0["K_joint"] < 1e-12 and r0["K_X"] < 1e-12


def test_L0_min_tv_to_incoherent_both_loops_and_if_arcs():
    # Build qP as an EXACT non-Markovian null point so a matching nm entry drives TV -> 0
    # (the `if tv < best[0]` True arc in the nm loop), while a decoy entry + the theta
    # sweep exercise the False arc. The grid loop's `if tv < best[0]` is hit True on the
    # first iteration (from 1e9) and False on later non-improving iterations.
    qP = nulls.axis_ad_null_point(p0=0.5, theta0=0.0, phi0=0.0,
                                  flip=0.15, p_lo=0.4, p_hi=1.6)["P_all"]

    # (a) empty nm_list (default) -> the `for ... in nm_list` NOT-ENTERED arc.
    tv_grid, desc_grid = nulls.min_tv_to_incoherent(qP)
    assert 0.0 <= tv_grid <= 1.0
    assert isinstance(desc_grid, str) and desc_grid.startswith("collective")
    # DISCRIMINATING: qP is a genuine NON-Markovian point, so the best MARKOVIAN-grid TV is
    # strictly POSITIVE (a mutant that shortcuts the grid `if tv<best` to always-True/always-
    # False, or corrupts tv, moves this). Pin it against an INDEPENDENT min over the grid
    # recomputed here (NOT calling min_tv_to_incoherent) using the module's tv_distance.
    _THETAS = tuple(i * math.pi / 6 for i in range(7))
    _PHIS = (0.0, math.pi / 2, math.pi)
    _PS = (0.05, 0.1, 0.2, 0.3, 0.45, 0.6, 0.8)
    best_ind = min(tv_distance(qP, nulls.axis_ad_null_point(p0=p, theta0=th, phi0=ph)["P_all"])
                   for th in _THETAS for ph in _PHIS for p in _PS)
    assert best_ind > 0.1                                    # qP is off the Markovian grid
    assert tv_grid == pytest.approx(best_ind, abs=1e-12)     # pin grid winner vs independent min
    assert tv_grid == pytest.approx(0.161521750, abs=1e-9)   # the specific value at these params

    # (b) non-empty nm_list -> ENTERED arc + the nm-loop `if tv<best` True (exact match,
    #     TV -> 0) and False (the decoy + non-matching theta) arcs.
    tv_nm, desc_nm = nulls.min_tv_to_incoherent(
        qP, nm_list=[(0.15, 0.4, 1.6), (0.45, 0.9, 1.1)])
    assert 0.0 <= tv_nm <= 1.0
    assert tv_nm == pytest.approx(0.0, abs=1e-9)      # the exact nm point matches qP
    assert desc_nm.startswith("nonmarkov")            # the nm point won
    assert tv_nm < tv_grid - 0.1                      # nm STRICTLY improves (was: <= grid; vacuous)
    # the exact nm point reproduces qP -> TV 0 vs an INDEPENDENT tv_distance recompute
    exact_match = nulls.axis_ad_null_point(p0=0.5, theta0=0.0, phi0=0.0,
                                           flip=0.15, p_lo=0.4, p_hi=1.6)["P_all"]
    assert tv_distance(qP, exact_match) == pytest.approx(0.0, abs=1e-12)


# =========================================================================== #
# L1 -- Hypothesis faithfulness properties                                     #
# =========================================================================== #
# Cheap null-point math (16-dim, nmax=1): generous example counts. The AD-family units
# take ~5-35 ms; the collective/GT dynamics units are pricier, so those L1 props stay
# lean (few crafted cases in L0 already pin them; Hypothesis here sweeps the cheap ones).

_ANG = st.floats(min_value=0.0, max_value=math.pi, allow_nan=False, allow_infinity=False)
_PHI = st.floats(min_value=0.0, max_value=2 * math.pi, allow_nan=False, allow_infinity=False)
_PROB = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)


@settings(max_examples=60, deadline=None)
@given(p0=_PROB, theta0=_ANG, phi0=_PHI)
def test_L1_axis_ad_markovian_is_cptp(p0, theta0, phi0):
    """Every Markovian axis-AD null is a valid record distribution (CPTP through the
    instrument): non-negative, normalized, K>=0."""
    _cptp_ok(nulls.axis_ad_null_point(p0=p0, theta0=theta0, phi0=phi0),
             expect_cmi_nonneg=True)


@settings(max_examples=40, deadline=None)
@given(p0=_PROB, theta0=_ANG, phi0=_PHI,
       flip=st.floats(min_value=0.0, max_value=1.0),
       p_lo=st.floats(min_value=0.0, max_value=2.0),
       p_hi=st.floats(min_value=0.0, max_value=2.0))
def test_L1_axis_ad_nonmarkovian_is_cptp_and_cmi_nonneg(p0, theta0, phi0, flip, p_lo, p_hi):
    """The non-Markovian (latent-modulated) axis-AD null stays a valid record
    distribution AND has non-negative CMI (a genuine information-theoretic quantity)."""
    _cptp_ok(nulls.axis_ad_null_point(p0=p0, theta0=theta0, phi0=phi0,
                                      flip=flip, p_lo=p_lo, p_hi=p_hi),
             expect_cmi_nonneg=True)


@settings(max_examples=60, deadline=None)
@given(p=_PROB)
def test_L1_classical_ad_is_cptp(p):
    _cptp_ok(nulls.classical_ad_null_point(p=p), expect_cmi_nonneg=True)


@settings(max_examples=40, deadline=None)
@given(flip=st.floats(min_value=0.0, max_value=1.0),
       p_lo=_PROB, p_hi=_PROB)
def test_L1_classical_nonmarkov_ad_is_cptp_and_cmi_nonneg(flip, p_lo, p_hi):
    _cptp_ok(nulls.classical_nonmarkov_ad_null_point(flip=flip, p_lo=p_lo, p_hi=p_hi),
             expect_cmi_nonneg=True)


@settings(max_examples=25, deadline=None)
@given(gamma_c=st.floats(min_value=0.0, max_value=1.5,
                         allow_nan=False, allow_infinity=False),
       tau=st.floats(min_value=0.0, max_value=2.0,
                     allow_nan=False, allow_infinity=False))
def test_L1_collective_ad_is_cptp(gamma_c, tau):
    _cptp_ok(nulls.collective_ad_null_point(gamma_c=gamma_c, tau=tau),
             expect_cmi_nonneg=True)


@settings(max_examples=25, deadline=None)
@given(a0=_ANG, b0=_ANG, c0=_ANG, pa=_PROB, tha=_ANG)
def test_L1_coherent_ad_is_cptp(a0, b0, c0, pa, tha):
    """A coherent-unitary + axis-AD null (Markovian) is still a valid record
    distribution -- coherence generation does not break CPTP through the instrument."""
    _cptp_ok(nulls.coherent_ad_null_point(u0=(a0, b0, c0), u1=(c0, b0, a0),
                                          ad0=(pa, tha, 0.0), ad1=(pa, tha, 0.0),
                                          zz=b0),
             expect_cmi_nonneg=True)


@st.composite
def _joint64(draw):
    """A valid 3-round joint distribution over the 64 (X,Z) keys (>=0, sums to 1) -- an
    arbitrary record for the min-TV metric-range property."""
    keys = [(m1, m2, m3) for m1 in M_ALPHABET for m2 in M_ALPHABET for m3 in M_ALPHABET]
    raw = draw(st.lists(st.floats(min_value=0.0, max_value=1.0,
                                  allow_nan=False, allow_infinity=False),
                        min_size=len(keys), max_size=len(keys)))
    tot = sum(raw)
    if tot <= 1e-9:                              # degenerate all-zero draw -> uniform
        raw = [1.0] * len(keys)
        tot = float(len(keys))
    return {k: raw[i] / tot for i, k in enumerate(keys)}


@settings(max_examples=15, deadline=None)
@given(qP=_joint64())
def test_L1_min_tv_to_incoherent_in_unit_interval(qP):
    """min_tv_to_incoherent returns a TV in [0,1] for ANY valid record qP (it is a min of
    total-variation distances between probability distributions)."""
    tv, desc = nulls.min_tv_to_incoherent(qP, nm_list=[(0.2, 0.5, 1.5)])
    assert 0.0 - 1e-12 <= tv <= 1.0 + 1e-12
    assert isinstance(desc, str) and desc


@st.composite
def _gt_params(draw):
    """Physically-sensible shared-bath parameters for the *_gt closed-form checks."""
    return dict(
        zeta=draw(st.floats(min_value=0.1, max_value=2.0)),
        gamma=draw(st.floats(min_value=0.05, max_value=1.0)),
        g0z=draw(st.floats(min_value=0.0, max_value=0.4)),
        g1z=draw(st.floats(min_value=0.0, max_value=0.4)),
        tau=draw(st.floats(min_value=0.1, max_value=1.2)),
    )


@pytest.mark.skipif(os.environ.get("STAGE_D_SKIP_SLOW") == "1",
                    reason="slow Hypothesis(12) x nmax=16 convergence sweep; runs in the coverage "
                           "gate, skipped under MUTATION only -- the deterministic single-call "
                           "nmax=16 corner test (test_L1_indep_boson_nmax6_is_UNCONVERGED) kills the "
                           "same two_qubit_indep_boson_gt mutants fast")
@settings(max_examples=12, deadline=None)
@given(pp=_gt_params())
def test_L1_two_qubit_indep_boson_gt_recovers_closed_form(pp):
    """The reduced sigma_z-sector coherences equal the independent-boson closed form to
    machine precision, over a swept parameter band (worst_err -> 0).

    CONVERGENCE (reviewer 2026-07-07, HIGH -- flaky false-green fix). The tight <1e-8
    EXACTNESS claim only holds at an nmax large enough to hold the displaced-mode
    excitation. At the band corner (zeta=1,gamma=1,g0z=0.25,g1z=0.375,tau=1) nmax=6 gives
    worst_err=3.4e-8 > 1e-8 (a genuine truncation residual, NOT round-off), while nmax=16
    gives 8e-16. The old test asserted <1e-8 at nmax=6 and only passed because Hypothesis'
    example DB never replayed that corner. This asserts the exactness at the CONVERGED
    nmax=16 (where it truly holds over the whole band)."""
    r = gt.two_qubit_indep_boson_gt(nmax=16, **pp)
    assert r["worst_err"] < 1e-8


def test_L1_indep_boson_nmax6_is_UNCONVERGED_at_band_corner():
    """Guard the convergence claim itself (reviewer HIGH): the corner that broke the flaky
    test MUST show nmax=6 unconverged (>1e-8) and nmax=16 converged (<1e-12). If a future
    refactor made nmax=6 exact, the tightened nmax=16 assert above would be silently
    over-strict; this test would flag the shift. Deterministic (no Hypothesis DB)."""
    corner = dict(zeta=1.0, gamma=1.0, g0z=0.25, g1z=0.375, tau=1.0)
    err6 = gt.two_qubit_indep_boson_gt(nmax=6, **corner)["worst_err"]
    err16 = gt.two_qubit_indep_boson_gt(nmax=16, **corner)["worst_err"]
    assert err6 > 1e-8, f"nmax=6 unexpectedly converged at the corner: {err6}"
    assert err16 < 1e-12, f"nmax=16 not converged at the corner: {err16}"


@settings(max_examples=10, deadline=None)
@given(zeta=st.floats(min_value=0.1, max_value=2.0),
       gamma=st.floats(min_value=0.05, max_value=1.0),
       g=st.floats(min_value=0.0, max_value=0.4),
       tau=st.floats(min_value=0.1, max_value=1.2))
def test_L1_sigma_minus_emission_gt_recovers_amplitude_ode(zeta, gamma, g, tau):
    """The GKSL reduced p_e(t) equals the exact single-excitation amplitude ODE, swept
    (worst_err -> 0)."""
    r = gt.sigma_minus_emission_gt(nmax=5, zeta=zeta, gamma=gamma, g=g, tau=tau, n_t=3)
    assert r["worst_err"] < 1e-8


# =========================================================================== #
# KILLER (Side-A teeth) -- prove the load-bearing asserts DISCRIMINATE          #
# =========================================================================== #
def test_KILLER_cptp_norm_would_fail_for_non_trace_preserving_ad():
    # Sabotage: drop the E1 (|1>-><0| jump) Kraus so the per-round map is NOT
    # trace-preserving (only the E0 damping remains). The record mass then LEAKS below 1,
    # so the CPTP `sum(P_all) == 1` assert would BITE. (Real classical_ad_null_point has
    # both Kraus and sums to 1.)
    def _buggy_non_tp_ad(rho, p):
        s = math.sqrt(1.0 - p)
        E0 = np.array([[1.0, 0.0], [0.0, s]], dtype=complex)     # ONLY E0 (dropped E1)
        Eq0 = _on_qubit4(E0, 0)
        out = Eq0 @ rho @ Eq0.conj().T
        Eq1 = _on_qubit4(E0, 1)
        return Eq1 @ out @ Eq1.conj().T

    UX, UZ = _extract_x_full(1), _extract_z_full(1)
    rho0 = _initial_rho_dual(1)
    P = {}
    r1 = _buggy_non_tp_ad(rho0, 0.25)
    br1 = dual_extract(r1, 1, UX, UZ)
    for m1 in M_ALPHABET:
        a1 = br1[m1]
        r2 = _buggy_non_tp_ad(a1, 0.25)
        br2 = dual_extract(r2, 1, UX, UZ)
        for m2 in M_ALPHABET:
            a2 = br2[m2]
            r3 = _buggy_non_tp_ad(a2, 0.25)
            br3 = dual_extract(r3, 1, UX, UZ)
            for m3 in M_ALPHABET:
                P[(m1, m2, m3)] = float(np.trace(br3[m3]).real)
    real = nulls.classical_ad_null_point(p=0.25)
    assert abs(sum(real["P_all"].values()) - 1.0) < _NORM_TOL   # real: TP -> sum == 1
    assert sum(P.values()) < 1.0 - 1e-3                          # mutant: mass leaked (~0.45)


def test_KILLER_k_dropped_abs_would_fail_in_the_real_pipeline():
    # Finding LOW (reviewer 2026-07-07): the old KILLER used an ARTIFICIAL over-normalized
    # skip (sums to 2) so the signed sum was -1 -- an off-pipeline construction. On the REAL
    # pipeline both the marginal and the skip sum to ~1, so the SIGNED (dropped-abs) sum is
    # ~0 -- NOT negative, but ALSO nowhere near the true K. So the right in-pipeline tooth is
    # a VALUE pin: the real K_Z is a specific 0.09375 (independently recomputed), while a
    # dropped-abs mutant computes the signed sum ~0. We build the mutant IN-PIPELINE from the
    # real classical_ad P_all/P_skip and show it lands ~0, far from 0.09375.
    from error_coupling_simulator.quantum_bath.carrier import (
        _extract_x_full, _extract_z_full, _initial_rho_dual, dual_extract,
    )
    from error_coupling_simulator.quantum_bath.nulls import _ad_channel_data

    # rebuild the REAL classical_ad Z-axis (P_all, P_skip) exactly as the module does
    UX, UZ = _extract_x_full(1), _extract_z_full(1)
    rho0 = _initial_rho_dual(1)
    p = 0.25
    P_all, P_skip = {}, {}
    r1 = _ad_channel_data(rho0, p); br1 = dual_extract(r1, 1, UX, UZ)
    for m1 in M_ALPHABET:
        a1 = br1[m1]; r2 = _ad_channel_data(a1, p); br2 = dual_extract(r2, 1, UX, UZ)
        for m2 in M_ALPHABET:
            a2 = br2[m2]; r3 = _ad_channel_data(a2, p); br3 = dual_extract(r3, 1, UX, UZ)
            for m3 in M_ALPHABET:
                P_all[(m1, m2, m3)] = float(np.trace(br3[m3]).real)
        r_ev = _ad_channel_data(_ad_channel_data(a1, p), p); br_sk = dual_extract(r_ev, 1, UX, UZ)
        for m3 in M_ALPHABET:
            P_skip[(m1, m3)] = float(np.trace(br_sk[m3]).real)
    # project onto Z axis (the axis where AD-toward-Z imprints K)
    PaZ = {}
    for k, v in P_all.items():
        nk = tuple(m[1] for m in k); PaZ[nk] = PaZ.get(nk, 0.0) + v
    PsZ = {}
    for k, v in P_skip.items():
        nk = tuple(m[1] for m in k); PsZ[nk] = PsZ.get(nk, 0.0) + v

    real_KZ = float(sum(abs(sum(PaZ[(s1, s2, s3)] for s2 in (0, 1)) - PsZ[(s1, s3)])
                        for s1 in (0, 1) for s3 in (0, 1)))                       # WITH abs()
    mutant_KZ = float(sum((sum(PaZ[(s1, s2, s3)] for s2 in (0, 1)) - PsZ[(s1, s3)])
                          for s1 in (0, 1) for s3 in (0, 1)))                     # dropped abs()
    KZ_ind, _, _ = _indep_markov_KZ_KX(p)
    assert real_KZ == pytest.approx(KZ_ind, abs=1e-12)   # real: matches independent (0.09375)
    assert real_KZ > 0.09                                # a real, discriminable magnitude
    assert abs(mutant_KZ) < 1e-9                         # dropped-abs mutant collapses to ~0
    assert abs(real_KZ - mutant_KZ) > 0.09               # the abs() is load-bearing in-pipeline


def test_KILLER_gt_worst_err_would_fail_for_wrong_sign_exponent():
    # The independent-boson closed form is 0.25 exp(-(ds)^2 Gamma_unit). Sabotage: flip the
    # exponent sign to +(ds)^2 Gamma_unit. On a decohering (Gamma_unit>0) point the true
    # off-diagonals DECAY, so a +exp target no longer matches -> worst_err jumps well above
    # the 1e-9 grade. This proves the `worst_err -> 0` assert has teeth.
    nmax, zeta, gamma, g0z, g1z, tau = 6, 1.0, 0.3, 0.2, 0.15, 0.7
    E_red, dloc = round_superop(nmax, zeta, gamma, g0z, g1z, 0.0, 0.0, tau)
    plus = np.array([1.0, 1.0], dtype=complex) / math.sqrt(2.0)
    vac = np.zeros(nmax, dtype=complex); vac[0] = 1.0
    psi = np.kron(np.kron(plus, plus), vac)
    rho0 = np.outer(psi, psi.conj())
    rt = (E_red @ (rho0.T.reshape(-1))).reshape(dloc, dloc).T
    rho_dd = np.einsum("aibi->ab", rt.reshape(4, nmax, 4, nmax))
    Gamma_unit = gamma_unit_closed(tau, zeta, gamma)
    assert Gamma_unit > 1e-3, "test point must actually decohere for the tooth to bite"
    coup = {0: +1.0, 1: -1.0}

    def s_eig(a, b):
        return g0z * coup[a] + g1z * coup[b]

    worst_wrong = 0.0
    for row in range(4):
        a, b = (row >> 1) & 1, row & 1
        for col in range(4):
            ap, bp = (col >> 1) & 1, col & 1
            ds = s_eig(a, b) - s_eig(ap, bp)
            target_wrong = 0.25 * math.exp(+(ds * ds) * Gamma_unit)   # WRONG sign
            worst_wrong = max(worst_wrong, abs(abs(rho_dd[row, col]) - target_wrong))
    real = gt.two_qubit_indep_boson_gt(nmax=nmax, zeta=zeta, gamma=gamma,
                                       g0z=g0z, g1z=g1z, tau=tau)["worst_err"]
    assert real < _GT_EXACT                                     # real: recovers the form
    assert worst_wrong > 1e-3                                   # mutant: sign flip -> mismatch


def test_KILLER_tv_range_would_fail_for_dropped_half_factor():
    # TV = 0.5 * sum|Pa1-Pa2|. Dropping the 0.5 factor doubles it; for two record
    # distributions with disjoint support the sum|.| = 2 > 1, so a mutant TV would exceed
    # 1, VIOLATING the `min_tv in [0,1]` range. The real TV stays <= 1.
    qP = nulls.classical_nonmarkov_ad_null_point(flip=0.2, p_lo=0.1, p_hi=0.4)["P_all"]
    keys = list(qP)
    onekey = {k: (1.0 if k == keys[0] else 0.0) for k in qP}     # all mass on one key
    real_tv = tv_distance(qP, onekey)
    dropped_half = sum(abs(qP[k] - onekey[k]) for k in qP)       # mutant: no 0.5
    assert real_tv <= 1.0 + 1e-12                                # real: in [0,1]
    assert dropped_half > 1.0 + 1e-6                             # mutant: exceeds 1


# --------------------------------------------------------------------------- #
# KILLER (finding MEDIUM teeth) -- prove the NEW discriminating null-point pins  #
# BITE on wrong-but-CPTP channels. `_cptp_ok` alone passes for identity and a    #
# fixed random unitary (both CPTP); these run those two wrong channels through   #
# the SAME dual-axis instrument and show each discriminating pin fails on them   #
# while the real null passes. This is the mechanical proof the pins are not      #
# vacuous (the mutmut L2 gate is the automated form; this is the committed,      #
# always-on form -- and it does NOT depend on the mutation harness).             #
# --------------------------------------------------------------------------- #
def _run_wrong_channel(chan):
    """Push a caller-supplied (wrong) per-round channel through the real dual-axis
    instrument for 3 rounds, returning the same (K_X, K_Z, P_all) shape the nulls do."""
    UX, UZ = _extract_x_full(1), _extract_z_full(1)
    rho0 = _initial_rho_dual(1)
    P_all = {(m1, m2, m3): 0.0 for m1 in M_ALPHABET for m2 in M_ALPHABET for m3 in M_ALPHABET}
    P_skip = {(m1, m3): 0.0 for m1 in M_ALPHABET for m3 in M_ALPHABET}
    r1 = chan(rho0); br1 = dual_extract(r1, 1, UX, UZ)
    for m1 in M_ALPHABET:
        a1 = br1[m1]; r2 = chan(a1); br2 = dual_extract(r2, 1, UX, UZ)
        for m2 in M_ALPHABET:
            a2 = br2[m2]; r3 = chan(a2); br3 = dual_extract(r3, 1, UX, UZ)
            for m3 in M_ALPHABET:
                P_all[(m1, m2, m3)] = float(np.trace(br3[m3]).real)
        r_ev = chan(chan(a1)); br_sk = dual_extract(r_ev, 1, UX, UZ)
        for m3 in M_ALPHABET:
            P_skip[(m1, m3)] = float(np.trace(br_sk[m3]).real)
    PaX, PsX = project_axis(P_all, 0), project_axis(P_skip, 0)
    PaZ, PsZ = project_axis(P_all, 1), project_axis(P_skip, 1)
    return {"K_X": K_stat_binary(PaX, PsX), "K_Z": K_stat_binary(PaZ, PsZ), "P_all": P_all}


def test_KILLER_KZ_pin_would_fail_for_identity_channel():
    # WRONG-but-CPTP: identity per round (a no-AD channel). It is trace-preserving and
    # non-negative, so `_cptp_ok` passes -- but it imprints NO AD memory, so K_Z = 0. The
    # discriminating `K_Z == 0.09375` pin (real classical_ad p=0.25) therefore BITES.
    ident = _run_wrong_channel(lambda rho: rho)
    real = nulls.classical_ad_null_point(p=0.25)
    KZ_ind, _, _ = _indep_markov_KZ_KX(0.25)
    assert real["K_Z"] == pytest.approx(KZ_ind, abs=1e-12)   # real passes the pin
    assert abs(ident["K_Z"] - KZ_ind) > 0.09                 # identity FAILS the K_Z pin
    assert ident["K_Z"] < 1e-9                               # (identity: no AD memory at all)


def test_KILLER_KX_incoherence_pin_would_fail_for_random_unitary():
    # WRONG-but-CPTP: a fixed random 2-qubit UNITARY per round (deterministic seed). It is
    # CPTP, so `_cptp_ok` passes -- but a coherent unitary GENERATES complementary-axis
    # imprint, K_X ~ 0.30 >> 0. The discriminating `K_X < 1e-9` incoherence pin (which the
    # real incoherent-AD nulls satisfy) therefore BITES.
    rng = np.random.default_rng(12345)
    A = rng.standard_normal((4, 4)) + 1j * rng.standard_normal((4, 4))
    Q, _ = np.linalg.qr(A)
    U16 = np.kron(Q, np.eye(4, dtype=complex))               # unitary on data pair, I on ancillas
    runi = _run_wrong_channel(lambda rho: U16 @ rho @ U16.conj().T)
    real = nulls.classical_ad_null_point(p=0.25)
    assert real["K_X"] < 1e-9                                 # real incoherent: pin holds
    assert runi["K_X"] > 0.2                                  # random unitary FAILS the K_X pin


def test_KILLER_coherent_KX_pin_would_fail_if_unitary_dropped():
    # The coherent_ad null's coherence lives in its Ucoh step. A mutant that DROPS Ucoh
    # (keeping only the incoherent axis-AD) collapses K_X from ~0.237 to ~0. Emulate the
    # dropped-unitary variant as pure axis-AD with the same AD params, and show its K_X is
    # far from the real coherent K_X pin. (The real value is pinned in the L0 test.)
    real = nulls.coherent_ad_null_point(u0=(0.1, 0.2, 0.3), u1=(0.2, 0.1, 0.4),
                                        ad0=(0.2, 0.3, 0.4), ad1=(0.15, 0.5, 0.6), zz=0.3)
    dropped = nulls.axis_ad_null_point(p0=0.2, theta0=0.3, phi0=0.4,
                                       p1=0.15, theta1=0.5, phi1=0.6)   # NO unitary/zz
    assert real["K_X"] == pytest.approx(0.237284358806705, abs=1e-9)   # real coherence pin
    assert real["K_X"] > 0.2
    assert abs(dropped["K_X"] - real["K_X"]) > 0.2          # dropped-unitary mutant FAILS pin


def test_KILLER_cmi_pin_would_fail_for_markov_collapse():
    # The classical_nonmarkov null's memory (CMI ~ 0.0016) comes from the 2-state latent. A
    # mutant that collapses to the Markovian single-trajectory branch (ignores `flip`) gives
    # CMI = 0 (memoryless). The Markovian classical_ad is exactly that collapse -> CMI ~ 0,
    # far from the pinned 0.0016, so the discriminating CMI pin BITES.
    real = nulls.classical_nonmarkov_ad_null_point(flip=0.2, p_lo=0.1, p_hi=0.4)
    collapse = nulls.classical_ad_null_point(p=0.25)         # Markovian == latent ignored
    assert real["CMI"] == pytest.approx(0.001607490183685, abs=1e-12)   # real memory pin
    assert abs(collapse["CMI"]) < 1e-9                        # markov-collapse mutant FAILS pin
    assert real["CMI"] - abs(collapse["CMI"]) > 1e-3

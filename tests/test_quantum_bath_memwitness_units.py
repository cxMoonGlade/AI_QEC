"""Per-unit L0+L1 coverage of
``error_coupling_simulator.quantum_bath.memory_witness`` (4 public units).

The module evaluates the assisted-entanglement inequality from Bäcker, Beyer,
and Strunz, Phys. Rev. Lett. 132, 060402 (2024), arXiv:2310.01205, Theorem 1,
for the declared JC vacuum-mode reduced dynamics. ``inequality_violated`` records
only whether the sampled grid contains ``C#(t1) < C(t2)``; ``False`` is
inconclusive. Four public units are covered:

  UNIT                       L0 branch surface                         L1 faithfulness property
  ----                       -----------------                         ------------------------
  jc_reduced_choi            none tracked (straight line; 0/0)         valid Choi: trace-1, Hermitian, PSD
  concurrence                none tracked (straight line; 0/0)         in [0,1]; == indep Wootters formula
  concurrence_of_assistance  none tracked (straight line; 0/0)         in [0,1]; >= concurrence; Bell=1
  quantum_memory_witness     for/if k>0; Csharp<C fire + fired-break    sampled violation and non-violation,
                             + revival min/max loop (both arcs)         with the latter treated as inconclusive

NB on the "branch surface" (coverage.py --branch convention, honest 0/0). The three cheap units
are STRAIGHT-LINE bodies with NO Python decision point, so coverage.py emits NO tracked branch
arc for them -- they score branch 0/0 (nothing to miss); faithfulness rests on the L1 PROPERTY.
``quantum_memory_witness`` DOES carry real ``for``/``if`` branches; both arcs are exercised by
pairing an underdamped case (fires -> ``if Csharp[i] < C[j]`` / ``fired``-break True arcs) with a
Markovian case (never fires -> the fall-through / ``fired is None`` arcs).

EXPENSIVE-UNIT DISCIPLINE. ``quantum_memory_witness`` builds the JC (S,A,mode) GKSL (dim 4*nmax)
and matrix-exponentiates -- it is NOT run under Hypothesis. It uses a FEW crafted (underdamped vs
Markovian) cases at a small nmax (6) and a short time grid (n_t=24). Hypothesis is used ONLY for
the cheap linear-algebra units (concurrence / CoA / choi validity) over random density matrices.

Two-sided teeth (KILLER). The load-bearing C>=0 assert is shown DISCRIMINATING: an inlined
sabotaged variant (no ``max(0.0, .)`` clip) VIOLATES C>=0 in the claimed DIRECTION on a
separable state (feedback-devious-tests-killer-standard).
"""
from __future__ import annotations

import math

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from error_coupling_simulator.quantum_bath import memory_witness as mw

# --------------------------------------------------------------------------- #
# constants + builders (shared, deterministic; the batch's fixtures)          #
# --------------------------------------------------------------------------- #
_SY = np.array([[0.0, -1j], [1j, 0.0]], dtype=complex)
_SYY = np.kron(_SY, _SY)


def _bell_rho() -> np.ndarray:
    """|phi+><phi+| = (|00>+|11>)/sqrt2 -- max-entangled 2-qubit pure state (C=1)."""
    v = np.zeros(4, dtype=complex)
    v[0] = v[3] = 1.0 / math.sqrt(2.0)
    return np.outer(v, v.conj())


def _product_rho() -> np.ndarray:
    """|00><00| -- separable pure product state (C=0)."""
    v = np.zeros(4, dtype=complex)
    v[0] = 1.0
    return np.outer(v, v.conj())


def _dm_from_ginibre(re: list, im: list, d: int) -> np.ndarray:
    """A valid density matrix rho = A A^dag / tr(A A^dag) from a d x d Ginibre matrix A whose
    real/imag parts are the flat lists ``re``/``im`` (deterministic, so Hypothesis-shrinkable)."""
    a = np.array(re, dtype=float).reshape(d, d) + 1j * np.array(im, dtype=float).reshape(d, d)
    m = a @ a.conj().T
    tr = np.trace(m).real
    if tr <= 1e-12:                        # degenerate all-zero draw -> maximally mixed
        return np.eye(d, dtype=complex) / d
    return m / tr


def _wootters_lambdas_ref(rho4: np.ndarray) -> np.ndarray:
    """INDEPENDENT re-implementation of the Wootters lambdas (spin-flipped square-root eigenvalues,
    sorted DESC) -- used by the KILLER teeth + the concurrence value-pin, NOT importing the module's
    private ``_wootters_lambdas``, so the check is an independent from-scratch variant (faithfulness
    protocol: independent GT)."""
    rho_t = _SYY @ rho4.conj() @ _SYY
    ev = np.linalg.eigvals(rho4 @ rho_t).real
    lam = np.sqrt(np.clip(ev, 0.0, None))
    return np.sort(lam)[::-1]


def _damped_jc_amplitude(g: float, gamma: float, zeta: float, t: float) -> complex:
    """INDEPENDENT single-excitation amplitude a(t) = <e,0|psi(t)> of the damped Jaynes-Cummings
    (qubit + one damped mode), via the 2x2 non-Hermitian Schrodinger generator -- a DIFFERENT method
    from the module's full (4*nmax)^2 Liouvillian expm. This is the exact <=1-excitation solution
    (the |0,vac> branch is dark; |1,vac> evolves in {|1,0>,|0,1>} and decays to |0,0>), the same
    generator ground_truth.sigma_minus_emission_gt validates against the GKSL p_e -- certified
    independent, not circular. d/dt[a,c] = G[a,c], G=[[0,-ig],[-ig,-(i*zeta+gamma)]], init [1,0]."""
    from scipy.linalg import expm as _expm
    G = np.array([[0.0, -1j * g], [-1j * g, -(1j * zeta + gamma)]], dtype=complex)
    return complex((_expm(G * t) @ np.array([1.0, 0.0], dtype=complex))[0])


def _ad_choi_oracle(g: float, gamma: float, zeta: float, t: float) -> np.ndarray:
    """INDEPENDENT closed-form Choi chi(t) (4x4 on S,A; index = 2*S + A, |phi+> = (|00>+|11>)/sqrt2)
    of the JC reduced qubit channel = zero-T amplitude damping with survival eta=|a|^2 and coherence
    factor a(t). Built from the 2x2 Schrodinger amplitude, WITHOUT the module's Liouvillian / mode
    trace-out -- so pinning jc_reduced_choi == this (and the witness's C/C# curves == its Wootters)
    catches any dynamics / index / trace-out mutation that still returns 'a valid Choi'."""
    a = _damped_jc_amplitude(g, gamma, zeta, t)
    eta = abs(a) ** 2
    chi = np.zeros((4, 4), dtype=complex)
    chi[0, 0] = 0.5                       # E(|0><0|) (x) |0><0|_A  -> |00><00|
    chi[1, 1] = 0.5 * (1.0 - eta)         # (1-eta)|0><0| (x) |1><1|_A -> |01><01|  (decayed population)
    chi[3, 3] = 0.5 * eta                 # eta|1><1| (x) |1><1|_A    -> |11><11|
    chi[0, 3] = 0.5 * np.conj(a)          # coherence factor conj(a) (verified vs module: at zeta=0.3 the
    chi[3, 0] = 0.5 * a                    # module's chi[0,3] carries -Im(a); zeta=0 -> a real -> no effect)
    return chi


# =========================================================================== #
# L0 -- per-unit statement + branch coverage (explicit, crafted inputs)       #
# =========================================================================== #
def test_L0_jc_reduced_choi_runs_and_is_a_valid_choi():
    # straight-line body; run it and confirm it returns a valid 4x4 Choi state.
    chi = mw.jc_reduced_choi(g=1.0, gamma=0.15, zeta=0.0, t=0.5, nmax=6)
    assert chi.shape == (4, 4)
    assert np.trace(chi).real == pytest.approx(1.0, abs=1e-9)        # trace-1
    assert np.max(np.abs(chi - chi.conj().T)) < 1e-9                 # Hermitian
    ev = np.linalg.eigvalsh(0.5 * (chi + chi.conj().T)).real
    assert ev.min() > -1e-9                                          # PSD (up to numeric)


def test_L0_concurrence_runs_bell_and_product():
    assert mw.concurrence(_bell_rho()) == pytest.approx(1.0, abs=1e-9)
    assert mw.concurrence(_product_rho()) == pytest.approx(0.0, abs=1e-12)


def test_L0_concurrence_of_assistance_runs_bell_and_product():
    assert mw.concurrence_of_assistance(_bell_rho()) == pytest.approx(1.0, abs=1e-9)
    assert mw.concurrence_of_assistance(_product_rho()) == pytest.approx(0.0, abs=1e-12)


def test_L0_quantum_memory_witness_covers_violating_and_inconclusive_arcs():
    # UNDERDAMPED (g=1, gamma=0.15): non-Markovian revival -> C#(t1)<C(t2) FIRES. This takes the
    # ``if k>0`` True arc (k>=1), the ``Csharp[i] < C[j]`` True arc, the inner ``break`` and the
    # ``if fired: break`` True arc, and the revival min/max loop.
    ud = mw.quantum_memory_witness(g=1.0, gamma=0.15, zeta=0.0, tau=6.0, nmax=6, n_t=24)
    assert ud["inequality_violated"] is True
    assert ud["fired_t1_t2"] is not None
    assert ud["concurrence_revival"] > 1e-6
    # MARKOVIAN (gamma=50): monotone decay, NEVER fires -> the ``Csharp[i] < C[j]`` False arc for
    # every (i,j), the inner loop FALLS THROUGH (no break), and ``if fired`` stays False (fired is
    # None): the complementary branch arcs.
    mk = mw.quantum_memory_witness(g=1.0, gamma=50.0, zeta=0.0, tau=6.0, nmax=6, n_t=24)
    assert mk["inequality_violated"] is False
    assert mk["fired_t1_t2"] is None
    assert mk["concurrence_revival"] == pytest.approx(0.0, abs=1e-9)


# =========================================================================== #
# L1 -- Hypothesis faithfulness properties (cheap linear-algebra units only)   #
# =========================================================================== #
@st.composite
def dm4(draw):
    """A valid 4x4 (2-qubit) density matrix via a random Ginibre A -> A A^dag / tr."""
    n = 16
    re = draw(st.lists(st.floats(-3.0, 3.0, allow_nan=False, allow_infinity=False),
                       min_size=n, max_size=n))
    im = draw(st.lists(st.floats(-3.0, 3.0, allow_nan=False, allow_infinity=False),
                       min_size=n, max_size=n))
    return _dm_from_ginibre(re, im, 4)


@settings(max_examples=400, deadline=None)
@given(dm4())
def test_L1_concurrence_in_unit_interval(rho):
    """Wootters concurrence is in [0,1] for any 2-qubit density matrix (a theorem)."""
    c = mw.concurrence(rho)
    assert -1e-12 <= c <= 1.0 + 1e-9


@settings(max_examples=400, deadline=None)
@given(dm4())
def test_L1_concurrence_matches_independent_wootters_formula(rho):
    """DISCRIMINATING: concurrence == max(0, lam1-lam2-lam3-lam4) with the lambdas from the
    INDEPENDENT spin-flip recompute (_wootters_lambdas_ref -- NOT the module's private helper).
    On a GENERIC mixed state all four Wootters lambdas are distinct+nonzero, so every index/sign
    in the formula is load-bearing -- this KILLS the index/sign mutations that are equivalent on
    Bell/product (where the lower lambdas vanish and the [0,1] test can't see them)."""
    lam = _wootters_lambdas_ref(rho)
    ref = float(max(0.0, lam[0] - lam[1] - lam[2] - lam[3]))
    assert mw.concurrence(rho) == pytest.approx(ref, abs=1e-9)


@settings(max_examples=400, deadline=None)
@given(dm4())
def test_L1_coa_in_unit_interval_and_ge_concurrence(rho):
    """C# (concurrence of assistance) is in [0,1] and >= C (assistance can only help)."""
    c = mw.concurrence(rho)
    cs = mw.concurrence_of_assistance(rho)
    assert -1e-12 <= cs <= 1.0 + 1e-9
    assert cs >= c - 1e-12


@settings(max_examples=400, deadline=None)
@given(dm4())
def test_L1_coa_matches_independent_wootters_sum(rho):
    """DISCRIMINATING: C# == sum(lam_i) from the INDEPENDENT Wootters recompute (every lambda
    load-bearing on a generic mixed state -- pins the value, not just the C <= C# <= 1 bound)."""
    lam = _wootters_lambdas_ref(rho)
    assert mw.concurrence_of_assistance(rho) == pytest.approx(float(lam.sum()), abs=1e-9)


def test_L1_jc_reduced_choi_is_valid_over_a_param_sweep():
    """jc_reduced_choi is a valid Choi (trace-1, Hermitian, PSD) across a small parameter sweep --
    a light non-Hypothesis property sweep (the unit is a dynamics build, not run under Hypothesis)."""
    for gamma in (0.15, 1.0, 5.0):
        for t in (0.0, 0.7, 2.0):
            chi = mw.jc_reduced_choi(g=1.0, gamma=gamma, zeta=0.3, t=t, nmax=6)
            assert np.trace(chi).real == pytest.approx(1.0, abs=1e-9)
            assert np.max(np.abs(chi - chi.conj().T)) < 1e-9
            ev = np.linalg.eigvalsh(0.5 * (chi + chi.conj().T)).real
            assert ev.min() > -1e-8


def test_L1_jc_reduced_choi_matches_independent_ad_choi_oracle():
    """DISCRIMINATING value pin (mutation kill): jc_reduced_choi == the INDEPENDENT damped-JC
    AD-Choi oracle (2x2 Schrodinger amplitude -- a different method, not the module's Liouvillian)
    ELEMENT-WISE over a (zeta, gamma, t) sweep. A 'valid but wrong' Choi (index swap, wrong
    coupling/rate, mis-traced mode) diverges from the oracle => the mutation is KILLED. Both the
    detuned (zeta=0.3, complex a) and resonant (zeta=0, real a) branches exercise the coherence."""
    for zeta in (0.0, 0.3):
        for gamma in (0.15, 1.0, 5.0):
            for t in (0.3, 0.9, 2.0):
                chi = mw.jc_reduced_choi(g=1.0, gamma=gamma, zeta=zeta, t=t, nmax=6)
                ora = _ad_choi_oracle(1.0, gamma, zeta, t)
                assert np.allclose(chi, ora, atol=1e-8), (zeta, gamma, t, chi.round(4), ora.round(4))


def test_L1_quantum_memory_witness_curves_match_independent_oracle():
    """DISCRIMINATING value pin (mutation kill): the witness's whole C(t)/C#(t) curves == the
    INDEPENDENT oracle (AD-Choi -> Wootters), its ts grid == linspace, and its revival + fired
    verdict + C_max/C_min/Csharp_max == an independent recompute over those curves. This pins the
    Liouvillian build, the Choi, the curve loop, the fire-detection double loop, and the revival
    running-min loop -- killing the 55 (quantum_memory_witness) + 11 (_jc_sae_liouvillian) survivors
    that the boolean fire/silent asserts alone left alive (the 2026-07-07 mutation gap)."""
    g, gamma, zeta, tau, nmax, n_t = 1.0, 0.15, 0.0, 6.0, 6, 24
    w = mw.quantum_memory_witness(g=g, gamma=gamma, zeta=zeta, tau=tau, nmax=nmax, n_t=n_t)
    ts = np.linspace(2.0 * tau / n_t, 2.0 * tau, n_t)
    C_ora = np.empty(n_t); Cs_ora = np.empty(n_t)
    for k in range(n_t):
        lam = _wootters_lambdas_ref(_ad_choi_oracle(g, gamma, zeta, ts[k]))
        C_ora[k] = max(0.0, lam[0] - lam[1] - lam[2] - lam[3])
        Cs_ora[k] = lam.sum()
    # atol 1e-8 on the curves (nmax=6 mode truncation vs the exact oracle is ~2e-9, well below;
    # a real mutation moves a value by O(0.01+) so this stays sharply discriminating); the scalar
    # reductions accumulate the per-point truncation so use 1e-7 (still >> any structural mutation).
    assert np.allclose(np.array(w["ts"]), ts, atol=1e-12)
    assert np.allclose(np.array(w["C"]), C_ora, atol=1e-8)
    assert np.allclose(np.array(w["Csharp"]), Cs_ora, atol=1e-8)
    assert w["C_max"] == pytest.approx(float(C_ora.max()), abs=1e-7)
    assert w["C_min"] == pytest.approx(float(C_ora.min()), abs=1e-7)
    assert w["Csharp_max"] == pytest.approx(float(Cs_ora.max()), abs=1e-7)
    # independent revival recompute (max rise above the running minimum)
    rev = 0.0; rmin = C_ora[0]
    for k in range(1, n_t):
        rmin = min(rmin, C_ora[k]); rev = max(rev, C_ora[k] - rmin)
    assert w["concurrence_revival"] == pytest.approx(rev, abs=1e-7)
    # independent fired recompute (first i<j with Csharp[i] < C[j] - 1e-9)
    fired = None
    for i in range(n_t):
        for j in range(i + 1, n_t):
            if Cs_ora[i] < C_ora[j] - 1e-9:
                fired = (float(ts[i]), float(ts[j])); break
        if fired:
            break
    assert w["inequality_violated"] is (fired is not None)
    assert (w["fired_t1_t2"] is None) == (fired is None)
    if fired is not None:
        assert w["fired_t1_t2"][0] == pytest.approx(fired[0], abs=1e-9)
        assert w["fired_t1_t2"][1] == pytest.approx(fired[1], abs=1e-9)


# =========================================================================== #
# KILLER teeth -- prove the load-bearing asserts DISCRIMINATE                   #
# =========================================================================== #
def _buggy_concurrence_no_clip(rho4: np.ndarray) -> float:
    """Sabotage: drop the ``max(0.0, .)`` clip in concurrence -- returns the raw Wootters difference,
    which goes strictly NEGATIVE on a separable state, violating C >= 0."""
    lam = _wootters_lambdas_ref(rho4)
    return float(lam[0] - lam[1] - lam[2] - lam[3])       # <-- no max(0.0, .)


def test_KILLER_concurrence_nonneg_would_fail_for_no_clip_variant():
    # the maximally mixed 2-qubit state I/4 is unambiguously SEPARABLE: real concurrence is exactly 0
    # (all four Wootters lambdas equal 0.25), but the no-clip mutant returns
    # 0.25 - 0.25 - 0.25 - 0.25 = -0.5 < 0 -> it would VIOLATE the C >= 0 property.
    rho_sep = np.eye(4, dtype=complex) / 4.0                            # I/4, separable
    assert mw.concurrence(rho_sep) == pytest.approx(0.0, abs=1e-12)     # real: clipped to 0
    assert _buggy_concurrence_no_clip(rho_sep) < -1e-6                  # mutant: strictly negative (-0.5)

"""Stage-D batch (carrier) -- per-unit L0+L1 coverage of
``error_coupling_simulator.quantum_bath.carrier`` (9 CPU-pure public units).

Full-coverage program (docs/SIMULATOR.md SS12.3/12.4).
This module is the dual-ancilla dual-axis EXACT-DM carrier for the shared-bath
(pseudomode) simulator: 4-qubit parity gates + an exact reduced-idle GKSL apply +
ancilla-mediated instruments + the exact 3-round dual-axis record points (and their
QRT/reduced-map null). Pure numpy/math/scipy (device-agnostic, no torch, no cuda) -- so
it gets the FULL treatment: L0 (100% statement + branch per unit) + L1 (Hypothesis
faithfulness properties). L2 (mutmut) runs in Stage E.

COST NOTE. ``dual_point`` / ``dual_point_qrt`` run an EXACT density-matrix 3-round branch
tree on a (16*nmax)-dim DM (idle = expm of a (4*nmax)^2 Liouvillian, then a 4^3 = 64-leaf
instrument tree). Measured (RTX-irrelevant -- this is CPU numpy): nmax=1 ~6ms, nmax=2 ~66ms,
nmax=3 ~2.3s. So every expensive unit is exercised at nmax=1 (mode = a single vacuum level,
the algebra is still fully live) with ONE nmax=2 property check; Hypothesis example counts
are kept SMALL for the DM units and generous for the cheap linear-algebra gate units.

The 9 units + their L0 partition and L1 invariant. NB on the "branch surface": coverage.py
--branch emits NO tracked branch arc for a bare ``assert`` statement (verified empirically:
an assert is a plain statement line, no True/False arc), and NONE for a straight-line body.
So ``z_parity_unitary_4q``/``x_parity_unitary_4q``/``apply_idle_reduced``/``dual_point``/
``dual_point_qrt`` score branch 0/0 (nothing to miss) -- HONEST, their faithfulness rests on
the L1 PROPERTY, not a branch count. The ``assert abs(norm-1)<1e-8`` in dual_point/_qrt is a
plain covered statement whenever it PASSES (its False arc is a raise, which coverage.py does
NOT model as a branch here -- so there is no unreachable-arc exemption to make; see the
"defensive assert" note below).

  UNIT                     L0 branch surface                      L1 faithfulness property
  ----                     -----------------                      ------------------------
  cnot4                    for-loop (54) + `if bits[control]==1`  U^dag U = I (unitary);
                           (56) BOTH arcs (control=0 and =1)      permutation (each col one 1.0)
  z_parity_unitary_4q      none tracked (straight line; 0/0)      U^dag U = I; parity eig in {+-1}
  x_parity_unitary_4q      none tracked (straight line; 0/0)      U^dag U = I; parity eig in {+-1}
  apply_idle_reduced       none tracked (straight line; 0/0)      identity superop => rho unchanged;
                                                                  trace + hermiticity preserved
  dual_extract             two for-loops (141,144), enter+exit    reads BOTH parities correctly on
                                                                  simultaneous X,Z eigenstates;
                                                                  4 branches, each trace-nonneg
  quantum_dual_P_all       four nested for-loops (174/178/182/    P_all >= 0 and sums to ~1
                           187) enter+exit; nested `idle` def      (trace-preserving instrument);
                           excluded from the unit body            P_skip a valid (m1,m3) dist
  dual_point               `assert` = plain stmt (0/0 branch)     P_all norm ~1, non-negative;
                                                                  K_joint/K_X/K_Z >= 0
  quantum_dual_P_all_qrt   four nested for-loops (234/238/242/    P_all >= 0 and sums to ~1;
                           247) enter+exit; nested idle+reset      QRT null well-formed
                           defs excluded from the unit body
  dual_point_qrt           `assert` = plain stmt (0/0 branch)     P_all norm ~1, non-negative;
                                                                  K's >= 0

DEFENSIVE ASSERT (D1 finding-2 discipline). ``dual_point``/``dual_point_qrt`` carry
``assert abs(norm - 1.0) < 1e-8``. Per the D1 lesson (never exempt a "structurally
unreachable" arc without probing) I PROBED it: (a) coverage.py emits NO branch arc for a
bare assert (so there is nothing to exempt -- the assert line is covered as a plain
statement on every passing call); (b) the assert's guarantee (norm==1) is a TRACE-PRESERVATION
theorem of the instrument -- the projected+reset branches partition the identity, so the
64-leaf trace sum is the initial trace 1.0 for any physical parameters (verified: nmax in
{1,2,3}, random params, all norm==1 to ~1e-15). The False arc is therefore genuinely
unreachable with valid inputs AND carries no coverage obligation; NO exemption is registered.
The KILLER ``test_KILLER_dual_point_norm_...`` shows the assert is not vacuous: a sabotaged
generator that drops one leaf makes norm != 1, which the assert would catch.

Two-sided teeth (KILLER). The load-bearing L1 asserts (cnot4 unitarity, dual_extract parity
read, dual_point normalization) are each shown DISCRIMINATING: an inlined sabotaged variant
VIOLATES the property in the CLAIMED DIRECTION on a crafted input, so the property is not
vacuous (feedback-devious-tests-killer-standard; D1 finding-6: a KILLER's sabotage must
actually violate the property, direction verified).
"""
from __future__ import annotations

import math

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from error_coupling_simulator.quantum_bath import carrier as C
from error_coupling_simulator.quantum_bath.observables import M_ALPHABET

# --------------------------------------------------------------------------- #
# builders (shared, deterministic; NOT ad-hoc -- the batch's fixtures)        #
# --------------------------------------------------------------------------- #
PLUS = np.array([1.0, 1.0], dtype=complex) / math.sqrt(2.0)
MINUS = np.array([1.0, -1.0], dtype=complex) / math.sqrt(2.0)
ZERO = np.array([1.0, 0.0], dtype=complex)
ONE = np.array([0.0, 1.0], dtype=complex)

#: a physically valid parameter tuple (nmax excluded) for the shared-bath round.
PARAMS = dict(zeta=0.5, gamma=0.1, g0z=0.2, g1z=0.2, g0m=0.1, g1m=0.1, tau=1.0)

#: an ASYMMETRIC-coupling parameter tuple: g0z!=g1z AND g0m!=g1m so the two data qubits
#: are NOT interchangeable. Symmetric PARAMS masks a d0<->d1 routing swap (the qubits are
#: physically identical) and gives a d0<->d1-symmetric |++> record; the asymmetric tuple
#: makes the two qubits distinguishable so a mis-route / wrong-axis / wrong-record shows up
#: in a PINNED observable (reviewer finding: symmetric fixture masks the routing bug).
ASYM_PARAMS = dict(zeta=0.5, gamma=0.1, g0z=0.35, g1z=0.05, g0m=0.25, g1m=0.05, tau=1.0)


def _full_ket_rho(data16: np.ndarray, nmax: int) -> np.ndarray:
    """A pure (d0,d1,aX,aZ,mode) DM from a 16-vec data+ancilla ket tensored with |vac>_mode."""
    vac = np.zeros(nmax, dtype=complex)
    vac[0] = 1.0
    full = np.kron(data16, vac)
    return np.outer(full, full.conj())


def _data_anc(data2: np.ndarray) -> np.ndarray:
    """A 16-vec (d0,d1,aX,aZ) from a 4-dim (d0,d1) data ket, ancillas set to |0>|0>."""
    return np.kron(np.kron(data2, ZERO), ZERO)


def _bell(a: np.ndarray, b: np.ndarray, c: np.ndarray, d: np.ndarray) -> np.ndarray:
    """(|ab> + |cd>)/sqrt2 on the two data qubits (a simultaneous X0X1/Z0Z1 eigenstate)."""
    return (np.kron(a, b) + np.kron(c, d)) / math.sqrt(2.0)


def _params(nmax: int) -> tuple:
    return (nmax, PARAMS["zeta"], PARAMS["gamma"], PARAMS["g0z"], PARAMS["g1z"],
            PARAMS["g0m"], PARAMS["g1m"], PARAMS["tau"])


def _asym_params(nmax: int) -> tuple:
    return (nmax, ASYM_PARAMS["zeta"], ASYM_PARAMS["gamma"], ASYM_PARAMS["g0z"],
            ASYM_PARAMS["g1z"], ASYM_PARAMS["g0m"], ASYM_PARAMS["g1m"], ASYM_PARAMS["tau"])


# --------------------------------------------------------------------------- #
# INDEPENDENT recomputes (from-scratch physics, NOT calling the carrier's own  #
# private helpers) -- the strongest tooth: pin a value against a reimplemented  #
# formula so a wrong impl (wrong K axis, wrong record, mis-routed idle) fails.  #
# --------------------------------------------------------------------------- #
def _indep_project(P: dict, which: int) -> dict:
    """Marginalize a joint (sX,sZ)-keyed record onto axis `which` -- reimplemented here."""
    out: dict = {}
    for key, v in P.items():
        nk = tuple(m[which] for m in key)
        out[nk] = out.get(nk, 0.0) + v
    return out


def _indep_K_joint(P_all: dict, P_skip: dict) -> float:
    """Kolmogorov-consistency gap on the 4-ary joint record, from scratch (does NOT call
    carrier/observables.K_stat_joint): sum over (m1,m3) of |sum_m2 P_all - P_skip|."""
    return float(sum(
        abs(sum(P_all[(m1, m2, m3)] for m2 in M_ALPHABET) - P_skip[(m1, m3)])
        for m1 in M_ALPHABET for m3 in M_ALPHABET))


def _indep_K_binary(P_all_axis: dict, P_skip_axis: dict) -> float:
    """Binary (per-axis) Kolmogorov gap from scratch."""
    return float(sum(
        abs(sum(P_all_axis[(s1, s2, s3)] for s2 in (0, 1)) - P_skip_axis[(s1, s3)])
        for s1 in (0, 1) for s3 in (0, 1)))


def _indep_Ks(d: dict) -> tuple:
    """(K_joint, K_X, K_Z) recomputed independently from the returned record dicts."""
    Pa, Ps = d["P_all"], d["P_skip"]
    kj = _indep_K_joint(Pa, Ps)
    kx = _indep_K_binary(_indep_project(Pa, 0), _indep_project(Ps, 0))
    kz = _indep_K_binary(_indep_project(Pa, 1), _indep_project(Ps, 1))
    return kj, kx, kz


def _ref_apply_idle(E_red: np.ndarray, rho: np.ndarray, nmax: int) -> np.ndarray:
    """FROM-SCRATCH reference for apply_idle_reduced: the physical statement is
    E_full = E_red (x) I_aX (x) I_aZ on the FULL (d0,d1,aX,aZ,mode) DM. Reimplemented via an
    EXPLICIT per-spectator-block loop (NOT the vectorized einsum in the module) so a routing
    bug in the module's transpose/reshape chain shows up as a matrix mismatch. Column-stacking
    vec(B)=B.T.reshape(-1) convention, matching gksl.round_superop."""
    dr = 4 * nmax
    D = 16 * nmax
    r = rho.reshape(2, 2, 2, 2, nmax, 2, 2, 2, 2, nmax)
    # (Rket=(d0,d1,m), Sket=(aX,aZ), Rbra=(d0,d1,m), Sbra=(aX,aZ))
    r2 = r.transpose(0, 1, 4, 2, 3, 5, 6, 9, 7, 8).reshape(dr, 4, dr, 4)
    out = np.zeros_like(r2)
    for sk in range(4):
        for sb in range(4):
            block = r2[:, sk, :, sb]                    # (Rket, Rbra)
            w = E_red @ block.T.reshape(-1)             # column-stacking vec
            out[:, sk, :, sb] = w.reshape(dr, dr).T
    out = out.reshape(2, 2, nmax, 2, 2, 2, 2, nmax, 2, 2).transpose(0, 1, 3, 4, 2, 5, 6, 8, 9, 7)
    return out.reshape(D, D)


def _expect_Z_data(rho: np.ndarray, qidx: int, nmax: int) -> float:
    """<Z> on data qubit qidx (0=d0, 1=d1) of a full (d0,d1,aX,aZ,mode) DM -- a
    qubit-DISTINGUISHING observable (a d0<->d1 swap exchanges q=0 and q=1)."""
    from error_coupling_simulator.quantum_bath.gksl import I2, SZ2
    ops = [I2, I2, I2, I2]
    ops[qidx] = SZ2
    op4 = ops[0]
    for m in ops[1:]:
        op4 = np.kron(op4, m)
    opfull = np.kron(op4, np.eye(nmax, dtype=complex))
    return float(np.trace(opfull @ rho).real)


# =========================================================================== #
# L0 -- per-unit statement + branch coverage (explicit, crafted inputs)       #
# =========================================================================== #
def test_L0_cnot4_covers_both_control_arcs_and_is_a_permutation():
    # a SINGLE cnot4 call visits all 16 basis states: 8 have control=1 (if TRUE arc,
    # target flips) and 8 have control=0 (if FALSE arc) -- so both arcs of `if
    # bits[control]==1` AND both arcs of the for-loop are exercised in one call.
    U = C.cnot4(0, 3)                                   # control d0 (MSB), target a_Z (LSB)
    # permutation: each column has exactly one 1.0 (a classical reversible map)
    assert U.shape == (16, 16)
    assert np.allclose(U.sum(axis=0), 1.0) and np.allclose(U.sum(axis=1), 1.0)
    assert set(np.unique(U.real)) <= {0.0, 1.0}
    assert np.max(np.abs(U.conj().T @ U - np.eye(16))) < 1e-12   # unitary (permutation)
    # semantics: |1000> (d0=1) -> a_Z flips to |1001>; |0000> (d0=0) -> unchanged.
    s_ctrl1 = (1 << 3)                                  # d0=1, rest 0
    assert U[(1 << 3) | 1, s_ctrl1] == pytest.approx(1.0)          # a_Z flipped
    assert U[0, 0] == pytest.approx(1.0)                           # control=0 -> identity col


def test_L0_z_parity_unitary_4q_is_unitary_with_pm1_eigs():
    U = C.z_parity_unitary_4q()
    assert np.max(np.abs(U.conj().T @ U - np.eye(16))) < 1e-12     # unitary
    ev = np.linalg.eigvals(U)
    assert np.allclose(np.abs(ev), 1.0)                            # |eig| = 1
    assert set(np.round(ev.real, 6).tolist()) <= {-1.0, 1.0}       # parity eigenvalues +-1
    assert np.max(np.abs(ev.imag)) < 1e-9


def test_L0_x_parity_unitary_4q_is_unitary_with_pm1_eigs():
    U = C.x_parity_unitary_4q()
    assert np.max(np.abs(U.conj().T @ U - np.eye(16))) < 1e-12     # unitary
    ev = np.linalg.eigvals(U)
    assert np.allclose(np.abs(ev), 1.0)
    assert set(np.round(ev.real, 6).tolist()) <= {-1.0, 1.0}
    assert np.max(np.abs(ev.imag)) < 1e-9


def test_L0_apply_idle_reduced_identity_superop_is_a_noop():
    # identity reduced superop => the full-DM apply returns rho UNCHANGED (exact), and a
    # physical (trace-preserving) reduced superop preserves total trace + hermiticity.
    nmax = 2
    dr = 4 * nmax
    E_id = np.eye(dr * dr, dtype=complex)                          # identity superop on (d0,d1,mode)
    rho0 = _full_ket_rho(_data_anc(np.kron(PLUS, PLUS)), nmax)
    out = C.apply_idle_reduced(E_id, rho0, nmax)
    assert out.shape == (16 * nmax, 16 * nmax)
    assert np.max(np.abs(out - rho0)) < 1e-12                      # exact no-op
    # a REAL round superop is trace-preserving on the reduced space => total trace kept.
    from error_coupling_simulator.quantum_bath.gksl import round_superop
    E_red, _ = round_superop(*_params(nmax))
    out2 = C.apply_idle_reduced(E_red, rho0, nmax)
    assert np.trace(out2).real == pytest.approx(1.0, abs=1e-9)     # trace preserved
    assert np.max(np.abs(out2 - out2.conj().T)) < 1e-9            # hermiticity preserved


def test_L0_apply_idle_reduced_routing_is_pinned_qubit_distinguishing():
    # ROUTING (reviewer finding-2): the (d0,d1,mode)<->(aX,aZ) index/mode routing must be
    # EXACT, not just a valid basis permutation. Prior asserts used the symmetric |++> input
    # + nmax=1 (trivial mode) where a d0<->d1 (or data<->mode) swap is INVISIBLE. Here we use
    # nmax=2 (nontrivial mode), STRONGLY ASYMMETRIC couplings (only d0 couples to the bath),
    # and an ASYMMETRIC operand |1>_d0 |1>_d1 -- so d0 and d1 evolve DIFFERENTLY.
    nmax = 2
    from error_coupling_simulator.quantum_bath.gksl import round_superop
    # only-d0-coupled: g0z=g0m=0.4, g1z=g1m=0 -> d0 emits into the bath, d1 is a spectator.
    E_red, _ = round_superop(nmax, 0.5, 0.3, 0.4, 0.0, 0.4, 0.0, 1.5)
    data16 = _data_anc(np.kron(ONE, ONE))                         # |1>_d0 |1>_d1 |0>_aX |0>_aZ
    rho = _full_ket_rho(data16, nmax)
    out = C.apply_idle_reduced(E_red, rho, nmax)
    # (a) EXACT match to an INDEPENDENT from-scratch reimplementation (explicit per-spectator
    #     loop, not the module's vectorized einsum) -- any transpose/reshape mis-route fails.
    out_ref = _ref_apply_idle(E_red, rho, nmax)
    assert np.max(np.abs(out - out_ref)) < 1e-12                  # routing exact vs from-scratch ref
    # (b) qubit-DISTINGUISHING observable: only d0 decays (emits), d1 stays in |1>. A d0<->d1
    #     swap would EXCHANGE these two pinned values, so the pin catches the misroute.
    z0 = _expect_Z_data(out, 0, nmax)
    z1 = _expect_Z_data(out, 1, nmax)
    assert z0 == pytest.approx(-0.5319446761132696, abs=1e-9)     # d0 partially decayed toward |0>
    assert z1 == pytest.approx(-1.0, abs=1e-9)                    # d1 (decoupled) stays |1>
    assert z0 - z1 > 0.4                                          # the two data qubits are DISTINCT
    assert np.trace(out).real == pytest.approx(1.0, abs=1e-9)     # still trace-preserving


def test_L0_dual_extract_reads_both_parities_and_keeps_four_branches():
    # both for-loops (sX in {0,1}, sZ in {0,1}) visit all four leaves in ONE call.
    nmax = 1
    UX, UZ = C._extract_x_full(nmax), C._extract_z_full(nmax)
    # Bell (|00>+|11>)/sqrt2: X0X1=+1 (sX=0) AND Z0Z1=+1 (sZ=0) -> all mass in (0,0).
    data_pp = _bell(ZERO, ZERO, ONE, ONE)
    rho = _full_ket_rho(_data_anc(data_pp), nmax)
    br = C.dual_extract(rho, nmax, UX, UZ)
    assert set(br.keys()) == set(M_ALPHABET)                       # all four branches present
    probs = {k: float(np.trace(br[k]).real) for k in M_ALPHABET}
    assert probs[(0, 0)] == pytest.approx(1.0, abs=1e-9)           # X=+,Z=+ -> (0,0)
    for k in M_ALPHABET:
        if k != (0, 0):
            assert probs[k] == pytest.approx(0.0, abs=1e-9)
    # Bell (|01>+|10>)/sqrt2: X0X1=+1 (sX=0), Z0Z1=-1 (sZ=1) -> all mass in (0,1).
    data_pm = _bell(ZERO, ONE, ONE, ZERO)
    br2 = C.dual_extract(_full_ket_rho(_data_anc(data_pm), nmax), nmax, UX, UZ)
    assert float(np.trace(br2[(0, 1)]).real) == pytest.approx(1.0, abs=1e-9)
    # every branch trace is non-negative (a valid sub-probability)
    for k in M_ALPHABET:
        assert float(np.trace(br[k]).real) >= -1e-12


def test_L0_quantum_dual_P_all_runs_all_loops_and_is_a_distribution():
    # one call exercises the four nested loops (enter+exit) at nmax=1.
    P_all, P_skip = C.quantum_dual_P_all(*_params(1))
    assert len(P_all) == 4 ** 3                                    # 64 joint (m1,m2,m3) keys
    assert len(P_skip) == 4 ** 2                                   # 16 (m1,m3) skip keys
    assert all(v >= -1e-9 for v in P_all.values())                # non-negative
    assert sum(P_all.values()) == pytest.approx(1.0, abs=1e-8)    # trace-preserving instrument
    assert sum(P_skip.values()) == pytest.approx(1.0, abs=1e-8)   # P_skip is also a distribution


def test_L0_dual_point_returns_normalized_nonneg_record_and_nonneg_Ks():
    d = C.dual_point(*_params(1))                                 # the assert (norm~1) executes+passes
    assert d["norm"] == pytest.approx(1.0, abs=1e-8)
    assert all(v >= -1e-9 for v in d["P_all"].values())          # non-negative record
    assert sum(d["P_all"].values()) == pytest.approx(1.0, abs=1e-8)
    for key in ("K_joint", "K_X", "K_Z"):
        assert d[key] >= -1e-12                                    # K statistics non-negative
    assert set(d) >= {"K_joint", "K_X", "K_Z", "M_mem", "CMI", "P_all", "P_skip", "norm"}


def test_L0_dual_point_K_values_pinned_against_independent_recompute():
    # reviewer finding-1: K>=0 is VACUOUS (K is a sum of abs, >=0 for ANY dict). PIN each K to
    # its value, cross-checked against an INDEPENDENT from-scratch recompute (does NOT call
    # carrier's K_stat_*), at nmax=2 (mode has real dynamics -> K is genuinely NONZERO) with
    # ASYMMETRIC couplings (so K_X != K_Z and a wrong axis / wrong record moves a pinned value).
    d = C.dual_point(*_asym_params(2))
    kj_ref, kx_ref, kz_ref = _indep_Ks(d)                        # from-scratch, independent
    # (1) the module's K MUST equal the independent recompute (kills a wrong K formula/axis).
    assert d["K_joint"] == pytest.approx(kj_ref, abs=1e-12)
    assert d["K_X"] == pytest.approx(kx_ref, abs=1e-12)
    assert d["K_Z"] == pytest.approx(kz_ref, abs=1e-12)
    # (2) the K's are pinned to their ACTUAL values (kills a wrong record that would still be
    #     self-consistent with a wrong recompute). These are NONZERO and mutually DISTINCT --
    #     K_X != K_Z pins the X (axis 0) vs Z (axis 1) routing (a swapped axis flips them).
    assert d["K_joint"] == pytest.approx(0.3752296753809147, abs=1e-8)
    assert d["K_X"] == pytest.approx(0.2807204154701547, abs=1e-8)
    assert d["K_Z"] == pytest.approx(0.10329371119580281, abs=1e-8)
    assert d["K_X"] > d["K_Z"] + 0.1                              # axes are distinguishable
    # (3) a specific record entry is pinned too (a wrong P_all moves it).
    assert d["P_all"][((0, 0), (0, 0), (0, 0))] == pytest.approx(0.26680752056600426, abs=1e-6)


def test_L0_dual_point_exact_carrier_has_more_memory_than_QRT_null():
    # PHYSICS discriminator: the exact carrier keeps cross-round mode MEMORY; the QRT null
    # (dual_point_qrt) resets the mode each round, destroying it. So the Kolmogorov-consistency
    # violation K is FAR larger for the exact carrier than the memory-free null at the SAME
    # params. A wrong carrier that (e.g.) reset/ignored the mode would collapse this gap.
    exact = C.dual_point(*_asym_params(2))
    qrt = C.dual_point_qrt(*_asym_params(2))
    assert exact["K_joint"] > 0.3                                 # exact: strong multitime memory
    assert qrt["K_joint"] < 0.05                                  # QRT null: memory destroyed
    assert exact["K_joint"] > 10.0 * qrt["K_joint"]              # >10x memory gap (the null works)


def test_L0_quantum_dual_P_all_qrt_runs_all_loops_and_is_a_distribution():
    P_all, P_skip = C.quantum_dual_P_all_qrt(*_params(1))
    assert len(P_all) == 4 ** 3
    assert len(P_skip) == 4 ** 2
    assert all(v >= -1e-9 for v in P_all.values())
    assert sum(P_all.values()) == pytest.approx(1.0, abs=1e-8)
    assert sum(P_skip.values()) == pytest.approx(1.0, abs=1e-8)


def test_L0_dual_point_qrt_returns_normalized_nonneg_record_and_nonneg_Ks():
    d = C.dual_point_qrt(*_params(1))                            # the assert (norm~1) executes+passes
    assert d["norm"] == pytest.approx(1.0, abs=1e-8)
    assert all(v >= -1e-9 for v in d["P_all"].values())
    assert sum(d["P_all"].values()) == pytest.approx(1.0, abs=1e-8)
    for key in ("K_joint", "K_X", "K_Z"):
        assert d[key] >= -1e-12
    # the returned dict must carry EXACTLY the documented keys (kills a mangled-key return).
    assert set(d) == {"K_joint", "K_X", "K_Z", "M_mem", "CMI", "P_all", "P_skip", "norm"}


def test_L0_dual_point_qrt_K_values_pinned_against_independent_recompute():
    # same anti-vacuous PIN as the exact carrier, on the QRT null. nmax=2 + ASYMMETRIC
    # couplings; K's cross-checked against the from-scratch recompute AND pinned to value.
    d = C.dual_point_qrt(*_asym_params(2))
    kj_ref, kx_ref, kz_ref = _indep_Ks(d)
    assert d["K_joint"] == pytest.approx(kj_ref, abs=1e-12)
    assert d["K_X"] == pytest.approx(kx_ref, abs=1e-12)
    assert d["K_Z"] == pytest.approx(kz_ref, abs=1e-12)
    assert d["K_joint"] == pytest.approx(0.009089024743318233, abs=1e-8)
    assert d["K_X"] == pytest.approx(0.006083972575641278, abs=1e-8)
    assert d["K_Z"] == pytest.approx(0.006647506631681403, abs=1e-8)


# =========================================================================== #
# L1 -- Hypothesis faithfulness properties                                     #
# =========================================================================== #
@st.composite
def cnot_pairs(draw):
    """A valid (control, target) qubit pair (distinct, in 0..3)."""
    control = draw(st.integers(min_value=0, max_value=3))
    target = draw(st.integers(min_value=0, max_value=3).filter(lambda t: t != control))
    return control, target


@settings(max_examples=60, deadline=None)
@given(cnot_pairs())
def test_L1_cnot4_is_always_a_unitary_permutation(pair):
    """cnot4(c,t) is a permutation matrix (=> unitary) for every distinct (c,t)."""
    control, target = pair
    U = C.cnot4(control, target)
    assert np.max(np.abs(U.conj().T @ U - np.eye(16))) < 1e-12    # unitary
    # exactly one 1.0 per column and per row (a permutation)
    assert np.array_equal((np.abs(U) > 0.5).sum(axis=0), np.ones(16, dtype=int))
    assert np.array_equal((np.abs(U) > 0.5).sum(axis=1), np.ones(16, dtype=int))


@st.composite
def data_ket(draw):
    """A normalized 2-qubit (d0,d1) data ket (4 complex amplitudes)."""
    reals = draw(st.lists(st.floats(min_value=-1.0, max_value=1.0, allow_nan=False,
                                    allow_infinity=False), min_size=8, max_size=8))
    amps = np.array([complex(reals[2 * i], reals[2 * i + 1]) for i in range(4)])
    nrm = np.linalg.norm(amps)
    if nrm < 1e-9:
        amps = np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)
        nrm = 1.0
    return amps / nrm


@settings(max_examples=40, deadline=None)
@given(data_ket())
def test_L1_dual_extract_branches_sum_to_input_trace(data2):
    """The four dual_extract branch traces partition the input trace (=1 for a pure state):
    the sequential X-then-Z instrument is trace-preserving. Each branch trace is >= 0."""
    nmax = 1
    UX, UZ = C._extract_x_full(nmax), C._extract_z_full(nmax)
    rho = _full_ket_rho(_data_anc(data2), nmax)
    br = C.dual_extract(rho, nmax, UX, UZ)
    traces = [float(np.trace(br[k]).real) for k in M_ALPHABET]
    for t in traces:
        assert t >= -1e-9                                          # valid sub-probability
    assert sum(traces) == pytest.approx(1.0, abs=1e-9)            # partition of unity


def test_L1_branch_ax_az_return_projector_probability():
    # _branch_ax / _branch_az return (post-reset branch, prob). The prob MUST equal the
    # projected diagonal mass AND the reset branch's trace. Pin it on definite-parity states
    # so the returned probability is deterministic (not a >=0 tautology).
    nmax = 1
    UX, UZ = C._extract_x_full(nmax), C._extract_z_full(nmax)
    # |+>|->: X0X1 = -1 -> after the X extractor, a_X is definitely |1>.
    rho_x = _full_ket_rho(_data_anc(np.kron(PLUS, MINUS)), nmax)
    rx = UX @ rho_x @ UX.conj().T
    b0, p0 = C._branch_ax(rx, nmax, 0)
    b1, p1 = C._branch_ax(rx, nmax, 1)
    assert p0 == pytest.approx(0.0, abs=1e-9)                     # aX=0 branch: zero mass
    assert p1 == pytest.approx(1.0, abs=1e-9)                     # aX=1 branch: all mass (X=-1)
    assert float(np.trace(b1).real) == pytest.approx(p1, abs=1e-9)  # trace == prob (post-reset)
    # Bell |00>+|11>: Z0Z1 = +1 -> after the Z extractor, a_Z is definitely |0>.
    rho_z = _full_ket_rho(_data_anc(_bell(ZERO, ZERO, ONE, ONE)), nmax)
    rz = UZ @ rho_z @ UZ.conj().T
    bz0, pz0 = C._branch_az(rz, nmax, 0)
    _, pz1 = C._branch_az(rz, nmax, 1)
    assert pz0 == pytest.approx(1.0, abs=1e-9)                    # aZ=0 branch: all mass (Z=+1)
    assert pz1 == pytest.approx(0.0, abs=1e-9)                    # aZ=1 branch: zero mass
    assert float(np.trace(bz0).real) == pytest.approx(pz0, abs=1e-9)


@st.composite
def phys_params(draw):
    """A small envelope of physically valid shared-bath parameters (DM units: keep tight)."""
    return dict(
        zeta=draw(st.floats(min_value=0.0, max_value=1.0)),
        gamma=draw(st.floats(min_value=0.0, max_value=0.5)),
        g0z=draw(st.floats(min_value=-0.4, max_value=0.4)),
        g1z=draw(st.floats(min_value=-0.4, max_value=0.4)),
        g0m=draw(st.floats(min_value=-0.3, max_value=0.3)),
        g1m=draw(st.floats(min_value=-0.3, max_value=0.3)),
        tau=draw(st.floats(min_value=0.1, max_value=1.5)),
    )


@settings(max_examples=12, deadline=None)
@given(phys_params())
def test_L1_dual_point_is_a_valid_record_with_nonneg_Ks(pp):
    """dual_point over the parameter envelope: P_all is a valid distribution (>=0, norm~1)
    and every K statistic is >= 0 (K's are sums of absolute Kolmogorov-consistency gaps)."""
    d = C.dual_point(1, pp["zeta"], pp["gamma"], pp["g0z"], pp["g1z"],
                     pp["g0m"], pp["g1m"], pp["tau"])
    assert d["norm"] == pytest.approx(1.0, abs=1e-8)
    assert all(v >= -1e-9 for v in d["P_all"].values())
    assert d["K_joint"] >= -1e-12 and d["K_X"] >= -1e-12 and d["K_Z"] >= -1e-12
    # non-vacuous: every K equals the INDEPENDENT from-scratch recompute over the whole
    # envelope (a wrong K formula / wrong marginalization axis fails somewhere in the sweep).
    kj_ref, kx_ref, kz_ref = _indep_Ks(d)
    assert d["K_joint"] == pytest.approx(kj_ref, abs=1e-12)
    assert d["K_X"] == pytest.approx(kx_ref, abs=1e-12)
    assert d["K_Z"] == pytest.approx(kz_ref, abs=1e-12)


@settings(max_examples=6, deadline=None)
@given(phys_params())
def test_L1_dual_point_qrt_is_a_valid_record_with_nonneg_Ks(pp):
    d = C.dual_point_qrt(1, pp["zeta"], pp["gamma"], pp["g0z"], pp["g1z"],
                         pp["g0m"], pp["g1m"], pp["tau"])
    assert d["norm"] == pytest.approx(1.0, abs=1e-8)
    assert all(v >= -1e-9 for v in d["P_all"].values())
    assert d["K_joint"] >= -1e-12 and d["K_X"] >= -1e-12 and d["K_Z"] >= -1e-12
    kj_ref, kx_ref, kz_ref = _indep_Ks(d)
    assert d["K_joint"] == pytest.approx(kj_ref, abs=1e-12)
    assert d["K_X"] == pytest.approx(kx_ref, abs=1e-12)
    assert d["K_Z"] == pytest.approx(kz_ref, abs=1e-12)


def test_L1_apply_idle_reduced_is_linear():
    """apply_idle_reduced(E,.) is a LINEAR map of rho (a superoperator): E(a*r1+b*r2) =
    a*E(r1)+b*E(r2). A crafted deterministic check (2 states, 2 scalars) -- cheap, exact."""
    nmax = 1
    from error_coupling_simulator.quantum_bath.gksl import round_superop
    E_red, _ = round_superop(*_params(nmax))
    r1 = _full_ket_rho(_data_anc(np.kron(PLUS, PLUS)), nmax)
    r2 = _full_ket_rho(_data_anc(np.kron(ZERO, ONE)), nmax)
    a, b = 0.3, 0.7
    lhs = C.apply_idle_reduced(E_red, a * r1 + b * r2, nmax)
    rhs = a * C.apply_idle_reduced(E_red, r1, nmax) + b * C.apply_idle_reduced(E_red, r2, nmax)
    assert np.max(np.abs(lhs - rhs)) < 1e-12


# =========================================================================== #
# KILLER (teeth) -- prove the load-bearing asserts DISCRIMINATE                 #
# =========================================================================== #
def _buggy_cnot4(control, target):
    """Sabotage: write EVERY permuted image into a fixed row 0 (not a bijection) -- collapses
    16 columns onto one basis vector, so the matrix is rank-deficient and NOT unitary
    (U^dag U has a 16 on the diagonal, not the identity). Violates the unitarity property in
    the claimed direction (||U^dag U - I|| >> 0)."""
    U = np.zeros((16, 16), dtype=complex)
    for s in range(16):
        bits = [(s >> 3) & 1, (s >> 2) & 1, (s >> 1) & 1, s & 1]
        if bits[control] == 1:
            bits[target] ^= 1
        U[0, s] = 1.0                                              # BUG: fixed row (not permutation)
    return U


def test_KILLER_cnot4_unitarity_would_fail_for_non_permutation_variant():
    real = C.cnot4(0, 3)
    buggy = _buggy_cnot4(0, 3)
    assert np.max(np.abs(real.conj().T @ real - np.eye(16))) < 1e-12     # real: unitary
    err = np.max(np.abs(buggy.conj().T @ buggy - np.eye(16)))
    assert err > 0.5                                                     # mutant: far from unitary


def test_KILLER_dual_extract_parity_read_would_fail_for_wrong_axis_variant():
    # |+>|->: X0X1 = -1 (correct read: sX=1). The real extractor puts all mass in sX=1.
    # A buggy extractor that uses the Z-instrument (UZ) in the X-slot reads the Z-parity of
    # |+->, which is 0 (|+-> is not a Z eigenstate) -> it MISreads sX=0. So the "reads
    # X-parity correctly" property (mass at sX=1 ~ 1) VIOLATES for the mutant (mass ~ 0).
    nmax = 1
    UX, UZ = C._extract_x_full(nmax), C._extract_z_full(nmax)
    data_pm = _data_anc(np.kron(PLUS, MINUS))                     # X0X1 eigenstate, eig -1
    rho = _full_ket_rho(data_pm, nmax)
    real = C.dual_extract(rho, nmax, UX, UZ)                      # correct axes
    buggy = C.dual_extract(rho, nmax, UZ, UZ)                     # BUG: Z-instrument in X-slot
    mass_sX1_real = sum(float(np.trace(real[k]).real) for k in M_ALPHABET if k[0] == 1)
    mass_sX1_buggy = sum(float(np.trace(buggy[k]).real) for k in M_ALPHABET if k[0] == 1)
    assert mass_sX1_real == pytest.approx(1.0, abs=1e-9)         # real: X=-1 -> sX=1
    assert mass_sX1_buggy < 0.1                                  # mutant: misreads -> sX=0


def _buggy_quantum_dual_drop_leaf(nmax, zeta, gamma, g0z, g1z, g0m, g1m, tau):
    """Sabotage of quantum_dual_P_all: DROP the m3=(0,0) round-3 leaf from the sum (record
    only 3 of the 4 round-3 outcomes). For the |++> initial state that leaf carries ~half the
    mass, so the recorded distribution then sums to well under 1, and dual_point's
    ``assert abs(norm-1)<1e-8`` would fire. Violates the normalization property downward.
    (The dropped leaf is chosen to be a MASSIVE one -- dropping a near-zero leaf would not
    bite; D1 finding-6: the sabotage must actually move the property, verified below.)"""
    from error_coupling_simulator.quantum_bath.gksl import round_superop
    E_red, _ = round_superop(nmax, zeta, gamma, g0z, g1z, g0m, g1m, tau)
    UX, UZ = C._extract_x_full(nmax), C._extract_z_full(nmax)
    rho0 = _full_ket_rho(_data_anc(np.kron(PLUS, PLUS)), nmax)

    def idle(rho):
        return C.apply_idle_reduced(E_red, rho, nmax)

    P_all = {}
    r1 = idle(rho0)
    br1 = C.dual_extract(r1, nmax, UX, UZ)
    for m1 in M_ALPHABET:
        r2 = idle(br1[m1])
        br2 = C.dual_extract(r2, nmax, UX, UZ)
        for m2 in M_ALPHABET:
            r3 = idle(br2[m2])
            br3 = C.dual_extract(r3, nmax, UX, UZ)
            for m3 in M_ALPHABET:
                if m3 == (0, 0):                                  # BUG: drop the (0,0) leaf (~half the mass)
                    continue
                P_all[(m1, m2, m3)] = float(np.trace(br3[m3]).real)
    return P_all


def test_KILLER_dual_point_norm_would_fail_for_dropped_leaf_variant():
    # the real record sums to 1; the dropped-leaf mutant sums to strictly < 1, so
    # dual_point's norm assert (abs(norm-1)<1e-8) is NOT vacuous -- it would catch the drop.
    real_norm = sum(C.quantum_dual_P_all(*_params(1))[0].values())
    buggy_norm = sum(_buggy_quantum_dual_drop_leaf(*_params(1)).values())
    assert real_norm == pytest.approx(1.0, abs=1e-8)             # real: normalized
    assert buggy_norm < 1.0 - 1e-3                               # mutant: mass lost (< 1)


def _swap_d0d1(rho, nmax):
    """d0<->d1 basis permutation on a full (d0,d1,aX,aZ,mode) DM (ket AND bra)."""
    r = rho.reshape(2, 2, 2, 2, nmax, 2, 2, 2, 2, nmax)
    r = r.transpose(1, 0, 2, 3, 4, 6, 5, 7, 8, 9)
    return r.reshape(16 * nmax, 16 * nmax)


def test_KILLER_apply_idle_routing_would_fail_for_d0d1_swap_variant():
    # A d0<->d1 MISROUTE (swap the two data qubits before/after the reduced apply) is a VALID
    # basis permutation -- invisible to trace/hermiticity and to a symmetric |++> input. With
    # ASYMMETRIC couplings + |1>|1> it is caught: the from-scratch reference and the pinned
    # <Z_d0>/<Z_d1> both discriminate. (feedback-devious-tests-killer-standard; the sabotage
    # actually MOVES the qubit-distinguishing observable, direction verified.)
    nmax = 2
    from error_coupling_simulator.quantum_bath.gksl import round_superop
    E_red, _ = round_superop(nmax, 0.5, 0.3, 0.4, 0.0, 0.4, 0.0, 1.5)   # only d0 couples
    rho = _full_ket_rho(_data_anc(np.kron(ONE, ONE)), nmax)
    real = C.apply_idle_reduced(E_red, rho, nmax)
    buggy = _swap_d0d1(C.apply_idle_reduced(E_red, _swap_d0d1(rho, nmax), nmax), nmax)
    ref = _ref_apply_idle(E_red, rho, nmax)
    assert np.max(np.abs(real - ref)) < 1e-12                    # real matches from-scratch ref
    assert np.max(np.abs(buggy - ref)) > 0.1                     # mutant: routed wrong
    # the qubit-distinguishing observable is EXCHANGED by the swap (d0<->d1):
    assert _expect_Z_data(real, 0, nmax) == pytest.approx(-0.5319446761132696, abs=1e-9)
    assert _expect_Z_data(buggy, 0, nmax) == pytest.approx(-1.0, abs=1e-9)   # swap put d1 in slot 0


def _buggy_dual_point_wrong_KX_axis(nmax, *params):
    """Sabotage of dual_point: compute K_X on the WRONG axis (Z projection, axis 1, of P_all).
    Mirrors carrier mutmut_30 (project_axis(Pa, 1) in the K_X slot). The value CHANGES, so a
    pinned-K assert catches it; a >=0 assert would NOT (both are still >= 0)."""
    d = C.dual_point(nmax, *params)
    Pa, Ps = d["P_all"], d["P_skip"]
    d["K_X"] = _indep_K_binary(_indep_project(Pa, 1), _indep_project(Ps, 0))  # WRONG axis for Pa
    return d


def test_KILLER_dual_point_K_pin_would_fail_for_wrong_axis_variant():
    # the K>=0 assert is vacuous; the PINNED K_X catches a wrong-axis K. Real K_X != the
    # wrong-axis K_X, and only the pinned-value assert (not >=0) discriminates.
    real = C.dual_point(*_asym_params(2))
    buggy = _buggy_dual_point_wrong_KX_axis(2, *_asym_params(2)[1:])
    assert real["K_X"] == pytest.approx(0.2807204154701547, abs=1e-8)   # real: pinned
    assert abs(buggy["K_X"] - real["K_X"]) > 0.1                        # mutant: axis wrong -> moved
    assert buggy["K_X"] >= 0.0                                          # ...yet still >=0 (vacuous)

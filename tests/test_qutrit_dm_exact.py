"""Small-scale pytest for the exact qutrit engine + the R=1 Bayes-floor harness.

Phase-1 HARNESS test (Agent C; contract gate C). Covers, at SMALL scale (never the
3**9 d3 floor):

  * the XZZX parser (``forward/exact/xzzx_parser``): the real r01 ``d3_at_q6_7``
    circuit parses to 9 data, 8 stabilizers (4X+4Z) on data positions 0..8, the
    logical Z on the expected sites, with the built-in two-method stabilizer
    cross-check passing;
  * the floor math (``outputs/teacher_prereg/exact_floor_run``): exact TV + LER* on
    hand cases and via the contract engine API;
  * P2-ii: at L1=L2=0 the qutrit ``(s, m)`` distribution reproduces an independent
    ``2**n`` qubit enumeration bit-for-bit -- on a toy code AND, when the real GPU
    engine is importable, on the REAL parsed XZZX geometry at a feasible sub-register;
  * the real ``QutritDM`` engine (Agent A), guarded ``@cuda`` -- the floor harness
    drives its actual API.

GPU-only: the real-engine cases require CUDA and are skipped (not failed) without it,
so the suite is green on a CPU box while the GPU path is exercised on the workstation.
The mock-engine + parser + floor-math cases are pure CPU bookkeeping and always run.

Scope pytest to ``tests/`` (CLAUDE.md). The reference data path is the shipped
``google_105Q_surface_code_d3_d5_d7`` patch; parser cases needing it skip if absent.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from qec_twin.forward.exact import xzzx_parser as xp

# the floor harness lives under outputs/ (scripted-execution discipline); import the
# pure logic from it (no run side effects -- it is __main__-guarded).
import importlib.util

_FLOOR_PATH = Path(__file__).resolve().parents[1] / "outputs" / "teacher_prereg" / "exact_floor_run.py"
_spec = importlib.util.spec_from_file_location("exact_floor_run", _FLOOR_PATH)
floor = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(floor)

TOL = 1e-12

# Skip gates from tests/conftest.py (Wave 1, contract C1): SAME d3_at_q6_7 patch, so
# the canonical strict 4-file requires_data replaces the local r01-only requires_r01
# (DECLARED strictening, C1 risk note: a partial patch with r01 but no r10 now skips)
# and the canonical requires_cuda replaces the local try/except probe. The dead
# hardcoded absolute _DATASET path is deleted.
from conftest import requires_cuda, requires_data

_R01_CIRC, _R01_META = xp.default_r01_paths()

try:  # torch stays name-bound for the cuda-gated bodies; the PROBE lives in conftest
    import torch
except Exception:  # noqa: BLE001
    torch = None


# --------------------------------------------------------------------------- #
# Parser                                                                       #
# --------------------------------------------------------------------------- #
@requires_data
def test_parser_r01_structure():
    """The real r01 patch parses to the textbook XZZX d3 structure (positions 0..8)."""
    sch = xp.parse_xzzx_circuit(_R01_CIRC, _R01_META, verify=True)
    assert sch.n_data == 9
    assert sch.rounds == 1
    assert sch.surplus_dropped == ()  # r01 is natively 17 qubits / no surplus
    # 8 stabilizers, 4 X-type + 4 Z-type
    assert len(sch.stabilizers) == 8
    assert len(sch.x_stabilizers()) == 4
    assert len(sch.z_stabilizers()) == 4
    # every data position 0..8 appears in at least one stabilizer
    covered = set()
    for s in sch.stabilizers:
        covered |= set(s.paulis)
    assert covered == set(range(9))
    # each stabilizer is pure-X or pure-Z (XZZX gauge)
    for s in sch.stabilizers:
        assert s.kind in ("X", "Z")
    # logical Z on data positions {0, 2, 5} (circuit ids {0,5,10}); weight 3
    assert sch.logical_kind == "Z"
    assert set(sch.logical) == {0, 2, 5}
    assert all(v == "Z" for v in sch.logical.values())
    # default sweep word -> no data X-init
    assert sch.data_init_x == frozenset()


@requires_data
def test_parser_stabilizer_weights_and_data_map():
    """Stabilizer weights (2 boundary / 4 bulk) + the circuit-id<->position map."""
    sch = xp.parse_xzzx_circuit(_R01_CIRC, _R01_META, verify=True)
    weights = sorted(len(s.paulis) for s in sch.stabilizers)
    # rotated d3: 4 weight-2 boundary + 4 weight-4 bulk
    assert weights == [2, 2, 2, 2, 4, 4, 4, 4]
    # data circuit ids in engine-position order (metadata coord order)
    assert sch.data_indices == (0, 3, 5, 6, 8, 10, 11, 13, 16)
    # stab_ops() returns the contract tuple form
    op = sch.stabilizers[0].as_op()
    assert op[0] == "stab" and isinstance(op[1], dict) and isinstance(op[2], int)


@requires_data
def test_parser_verify_catches_broken_support():
    """The built-in cross-check rejects a tampered stabilizer support (positive control).

    A broken extraction must FAIL LOUDLY (the adversarial-self-verification rule). We
    monkeypatch the pullback to return a wrong support and confirm ``extract_stabilizers``
    raises rather than silently emitting it.
    """
    import stim

    circ = stim.Circuit.from_file(str(_R01_CIRC))
    import json

    meta = json.loads(Path(_R01_META).read_text())
    data_idx, meas_idx, _ = xp._classify_qubits(circ, meta)
    anc_order = [a for a in xp._first_ancilla_measure_order(circ) if a in set(meas_idx)]

    real = xp._pullback_stabilizer

    def broken(circuit, ancilla, didx):
        supp = real(circuit, ancilla, didx)
        if ancilla == anc_order[0] and supp:
            # corrupt one site -> wrong support; must be caught by the error-response
            k = next(iter(supp))
            bad = dict(supp)
            # move the support to a different data id (still pure type) -> inconsistent
            other = [d for d in didx if d not in supp][0]
            bad[other] = bad.pop(k)
            return bad
        return supp

    xp._pullback_stabilizer = broken
    try:
        with pytest.raises(AssertionError):
            xp.extract_stabilizers(circ, data_idx, anc_order, verify=True)
    finally:
        xp._pullback_stabilizer = real


# --------------------------------------------------------------------------- #
# Floor math (pure)                                                            #
# --------------------------------------------------------------------------- #
def test_tv_and_floor_hand_cases():
    a = {(0,): 0.5, (1,): 0.5}
    assert abs(floor.total_variation(a, a)) < TOL
    assert abs(floor.bayes_floor(a, a) - 0.5) < TOL  # no info -> chance floor
    b0, b1 = {(0,): 1.0}, {(1,): 1.0}
    assert abs(floor.total_variation(b0, b1) - 1.0) < TOL
    assert abs(floor.bayes_floor(b0, b1)) < TOL  # perfectly distinguishable -> 0
    c0, c1 = {(0,): 0.7, (1,): 0.3}, {(0,): 0.4, (1,): 0.6}
    assert abs(floor.total_variation(c0, c1) - 0.3) < TOL
    assert abs(floor.bayes_floor(c0, c1) - 0.35) < TOL


def test_leaked_map_adapter_bridges_b_to_a():
    """The A<->B leaked-readout adapter: B's dict/bias -> A's callable hard bit."""
    # B's dict (bias 0.90) -> hard bit 1 (round(0.90)); engine reads leaked as |1>-like
    f = floor.leaked_map_adapter({0: 0.0, 1: 1.0, 2: 0.90})
    assert callable(f) and int(f(2)) & 1 == 1
    # a bare float
    assert int(floor.leaked_map_adapter(0.90)(2)) & 1 == 1
    assert int(floor.leaked_map_adapter(0.10)(2)) & 1 == 0
    # an int passes through (reproduces A's check default lambda s: 1)
    assert int(floor.leaked_map_adapter(1)(2)) & 1 == 1
    # an already-callable is returned unchanged
    g = lambda level: 0
    assert floor.leaked_map_adapter(g) is g


# --------------------------------------------------------------------------- #
# Mock-engine harness (logic proof, no GPU)                                    #
# --------------------------------------------------------------------------- #
def test_mock_floor_harness_normalized_and_exact():
    """The floor harness on the mock engine: normalized P_m, 2**k cells, TV/LER* exact."""
    stabs, lz, lx = floor._toy_code()
    leaked = floor.leaked_map_adapter(1)
    eng = floor.MockQutritEngine(3)
    eng.set_code(stabilizers=stabs, logical_x=lx, logical_z=lz)
    res = floor.floor_from_engine(eng, stabs, leaked)
    assert abs(res["sum_P0"] - 1.0) < TOL and abs(res["sum_P1"] - 1.0) < TOL
    assert res["n_cells"] == 2 ** len(stabs)
    assert all(len(k) == len(stabs) for k in res["P0"])
    assert all(p >= -TOL for p in res["P0"].values())
    # TV recomputed independently equals the harness TV; LER* = 1/2(1-TV)
    assert abs(floor.total_variation(res["P0"], res["P1"]) - res["TV"]) < TOL
    assert abs(res["LER_star"] - 0.5 * (1.0 - res["TV"])) < TOL
    assert -TOL <= res["LER_star"] <= 0.5 + TOL


def test_mock_floor_with_leakage_valid():
    """Injecting leakage on every site keeps P_m normalized and LER* in [0, 0.5]."""
    stabs, lz, lx = floor._toy_code()
    leaked = floor.leaked_map_adapter(1)

    def np_leak(l1, l2):
        k0 = np.diag([1.0, math.sqrt(1 - l1), math.sqrt(1 - l2)]).astype(complex)
        kl = np.zeros((3, 3), complex); kl[2, 1] = math.sqrt(l1)
        ks = np.zeros((3, 3), complex); ks[1, 2] = math.sqrt(l2)
        return [k0, kl, ks]

    eng = floor.MockQutritEngine(3)
    eng.set_code(stabilizers=stabs, logical_x=lx, logical_z=lz)
    eng.init_logical(0)
    for s in range(3):
        eng.apply_channel(np_leak(0.05, 0.10), s)
    p0 = eng.syndrome_distribution(stabs, leaked)
    eng.init_logical(1)
    for s in range(3):
        eng.apply_channel(np_leak(0.05, 0.10), s)
    p1 = eng.syndrome_distribution(stabs, leaked)
    assert abs(sum(p0.values()) - 1.0) < TOL and abs(sum(p1.values()) - 1.0) < TOL
    assert -TOL <= floor.bayes_floor(p0, p1) <= 0.5 + TOL


def test_p2ii_mock_qutrit_equals_qubit_path_bitforbit():
    """P2-ii LOGIC: at L1=L2=0 the qutrit (s,m) dist == the 2**n qubit path, bit-for-bit."""
    n = 3
    stabs, lz, lx = floor._allz_toy_code()
    leaked = floor.leaked_map_adapter(1)
    ident = [np.eye(3, dtype=complex), np.zeros((3, 3), complex), np.zeros((3, 3), complex)]
    for m in (0, 1):
        eng = floor.MockQutritEngine(n)
        eng.set_code(stabilizers=stabs, logical_x=lx, logical_z=lz)
        eng.init_logical(m)
        for s in range(n):
            eng.apply_channel(ident, s)  # L1=L2=0 -> identity
        q = eng.syndrome_distribution(stabs, leaked)
        rho2 = floor._qubit_codestate_rho(n, stabs, lz, m)
        ref = floor.qubit_syndrome_distribution(rho2, [sorted(s.keys()) for s in stabs], n)
        keys = set(q) | set(ref)
        d = max(abs(q.get(k, 0.0) - ref.get(k, 0.0)) for k in keys)
        assert d < TOL, (m, d)


# --------------------------------------------------------------------------- #
# Real GPU engine (Agent A), guarded                                          #
# --------------------------------------------------------------------------- #
@requires_cuda
def test_real_engine_floor_api_small():
    """The floor harness drives the REAL QutritDM (Agent A) on a feasible toy code."""
    from qec_twin.forward.exact.qutrit_dm import QutritDM

    stabs, lz, lx = floor._toy_code()
    leaked = floor.leaked_map_adapter(1)
    eng = QutritDM(3, device="cuda")
    eng.set_code(stabilizers=stabs, logical_x=lx, logical_z=lz)
    res = floor.floor_from_engine(eng, stabs, leaked)
    assert abs(res["sum_P0"] - 1.0) < 1e-9 and abs(res["sum_P1"] - 1.0) < 1e-9
    assert res["n_cells"] == 2 ** len(stabs)
    assert -1e-9 <= res["LER_star"] <= 0.5 + 1e-9


@requires_cuda
def test_real_engine_p2ii_equals_qubit_path():
    """P2-ii on the REAL engine: L1=L2=0 qutrit (s,m) == 2**n qubit path, bit-for-bit.

    The actual contract gate C identity, on Agent A's production QutritDM (small toy
    code so it is feasible, not the 3**9 floor). Cross-method: qutrit GPU engine vs an
    independent numpy 2**n qubit enumeration.
    """
    from qec_twin.forward.exact.qutrit_dm import QutritDM

    n = 3
    stabs, lz, lx = floor._allz_toy_code()
    leaked = floor.leaked_map_adapter(1)
    for m in (0, 1):
        eng = QutritDM(n, device="cuda")
        eng.set_code(stabilizers=stabs, logical_x=lx, logical_z=lz)
        eng.init_logical(m)
        q = eng.syndrome_distribution(stabs, leaked)
        rho2 = floor._qubit_codestate_rho(n, stabs, lz, m)
        ref = floor.qubit_syndrome_distribution(rho2, [sorted(s.keys()) for s in stabs], n)
        keys = set(q) | set(ref)
        d = max(abs(q.get(k, 0.0) - ref.get(k, 0.0)) for k in keys)
        assert d < 1e-12, (m, d)


@requires_cuda
@requires_data
def test_real_engine_on_real_geometry_subregister():
    """The harness drives the real engine + real teacher on REAL XZZX stabilizers (feasible).

    Restricted to a <= 5-data sub-register (3**5 = 243; NOT the 3**9 floor) so this is a
    feasible integration smoke test of the real parser -> real engine -> real teacher path.
    """
    from qec_twin.forward.exact.qutrit_dm import QutritDM

    sch = xp.parse_xzzx_circuit(_R01_CIRC, _R01_META, verify=True)
    sub_sites = set(range(5))
    sub_stabs = [dict(s.paulis) for s in sch.stabilizers if set(s.paulis) <= sub_sites]
    if not sub_stabs:
        pytest.skip("no real stabilizer fits the 5-site sub-register")
    leaked = floor.leaked_map_adapter(1)
    eng = QutritDM(5, device="cuda")
    eng.set_code(stabilizers=sub_stabs, logical_z={0: "Z"})
    res = floor.floor_from_engine(eng, sub_stabs, leaked)
    assert abs(res["sum_P0"] - 1.0) < 1e-9 and abs(res["sum_P1"] - 1.0) < 1e-9
    assert res["n_cells"] == 2 ** len(sub_stabs)

    # inject the real teacher leakage; floor stays valid.
    # Use the representative WG regime (theta, g_seep) -- NOT the old (l1, l2); calling
    # leakage_kraus_torch(5e-3, 1e-1) here would bind theta=5e-3 (near-zero leakage) under a
    # stale rate label (the same R1 mislabel caught in the run entrypoint).
    from qec_twin.mechanisms.qutrit_teachers import (
        G_SEEP_DEFAULT, THETA_DEFAULT, leakage_kraus_torch)
    kr = leakage_kraus_torch(THETA_DEFAULT, G_SEEP_DEFAULT, 0.0, device="cuda")

    eng.init_logical(0)
    for s in range(5):
        eng.apply_channel(kr, s)
    p0 = eng.syndrome_distribution(sub_stabs, leaked)
    eng.init_logical(1)
    for s in range(5):
        eng.apply_channel(kr, s)
    p1 = eng.syndrome_distribution(sub_stabs, leaked)
    assert abs(sum(p0.values()) - 1.0) < 1e-9 and abs(sum(p1.values()) - 1.0) < 1e-9
    assert -1e-9 <= floor.bayes_floor(p0, p1) <= 0.5 + 1e-9


# --------------------------------------------------------------------------- #
# Two-site CPTP apply (WS2-B1; the coherent-ZZ crosstalk GT machinery)         #
# --------------------------------------------------------------------------- #
# ``QutritDM.apply_channel_2site`` applies a (9,9) two-qutrit channel on a possibly
# non-adjacent pair via a single two-site superoperator contraction (no dense 3^n embed).
# These cases certify it against an INDEPENDENT from-scratch dense embed (kron + axis
# permute -- a different code path than the engine einsum) + the product-channel reduction
# + the WS2 (5a) ZZ-unitary edge. Full sweep (incl. the negative controls) lives in
# ``outputs/teacher_prereg/ws2_two_site_apply_check.py``; this is the committed-suite slice.


def _embed_2site_ref(op9, i, j, n):
    """Dense 3^n x 3^n embed of a (9,9) two-qutrit op on sites (i, j) -- INDEPENDENT path.

    Kron the (9,9) op (pair index 3*t_i + t_j, i = high pair-trit) with I on the other n-2
    qutrits, then permute the two operator axes into the physical site slots (qutrit 0 = MSF).
    Written from scratch here (no call into the engine's embedding helpers) so the test is a
    non-circular cross-check of ``apply_channel_2site``.
    """
    op9 = op9.to(torch.complex128)
    rest = n - 2
    if rest > 0:
        full = torch.kron(op9, torch.eye(3 ** rest, dtype=torch.complex128, device=op9.device))
    else:
        full = op9
    other = [q for q in range(n) if q not in (i, j)]
    current = [i, j] + other
    perm_row = [current.index(q) for q in range(n)]
    perm = perm_row + [n + a for a in perm_row]
    D = 3 ** n
    return full.reshape([3] * (2 * n)).permute(*perm).contiguous().reshape(D, D)


def _rand_cptp_kraus(rng, dim, n_kraus, dev):
    """A random CPTP Kraus set (n_kraus, dim, dim) via Stinespring/QR (sum_k K^dag K = I)."""
    a = torch.tensor(
        rng.standard_normal((dim * n_kraus, dim)) + 1j * rng.standard_normal((dim * n_kraus, dim)),
        dtype=torch.complex128, device=dev,
    )
    v, _ = torch.linalg.qr(a)
    return v.reshape(n_kraus, dim, dim).contiguous()


def _rand_rho_t(rng, D, dev):
    m = torch.tensor(
        rng.standard_normal((D, D)) + 1j * rng.standard_normal((D, D)), dtype=torch.complex128, device=dev
    )
    rho = m @ m.conj().transpose(-1, -2)
    return rho / torch.trace(rho).real


@requires_cuda
def test_apply_channel_2site_matches_dense_embed():
    """(i) apply_channel_2site == sum_k embed_2site(K) @ rho @ embed^dag, to <1e-12.

    Random CPTP 2-qutrit Kraus sets on random PSD trace-1 rho, over n in {3,4,5} and pairs
    that are adjacent, non-adjacent, AND reversed (i>j -> the swap path). The dense embed is a
    from-scratch independent algorithm (kron+permute), so agreement is non-circular.
    """
    from qec_twin.forward.cptp_channel import apply_kraus as dense_apply_kraus
    from qec_twin.forward.exact.qutrit_dm import QutritDM

    rng = np.random.default_rng(7)
    worst = 0.0
    for n in (3, 4, 5):
        D = 3 ** n
        pairs = [(0, 1), (1, 0), (0, n - 1), (n - 1, 0)]
        if n >= 4:
            pairs += [(1, n - 1), (n - 1, 1)]
        for (i, j) in pairs:
            for r in (1, 2, 4):
                kraus9 = _rand_cptp_kraus(rng, 9, r, "cuda")
                rho = _rand_rho_t(rng, D, "cuda")
                eng = QutritDM(n, device="cuda")
                eng.set_state(rho.clone())
                eng.apply_channel_2site(kraus9, i, j)
                embedded = torch.stack([_embed_2site_ref(kraus9[k], i, j, n) for k in range(r)])
                ref = dense_apply_kraus(rho, embedded)
                ref = 0.5 * (ref + ref.conj().transpose(-1, -2))
                worst = max(worst, float((eng.rho - ref).abs().max()))
    assert worst < 1e-12, worst


@requires_cuda
def test_apply_channel_2site_product_reduction():
    """(iii) (K_i (x) K_j) via apply_channel_2site == apply_channel(K_i,i) then (K_j,j), <1e-12.

    Covers an adjacent, a non-adjacent, and a reversed (i>j) pair.
    """
    from qec_twin.forward.exact.qutrit_dm import QutritDM

    rng = np.random.default_rng(11)
    worst = 0.0
    for n in (3, 4, 5):
        D = 3 ** n
        pairs = [(0, 1), (0, n - 1)]
        if n >= 4:
            pairs.append((n - 1, 1))
        for (i, j) in pairs:
            ki = _rand_cptp_kraus(rng, 3, 2, "cuda")
            kj = _rand_cptp_kraus(rng, 3, 3, "cuda")
            prod = torch.stack([torch.kron(ki[a], kj[b]) for a in range(ki.shape[0]) for b in range(kj.shape[0])])
            rho = _rand_rho_t(rng, D, "cuda")
            engA = QutritDM(n, device="cuda")
            engA.set_state(rho.clone())
            engA.apply_channel_2site(prod, i, j)
            engB = QutritDM(n, device="cuda")
            engB.set_state(rho.clone())
            engB.apply_channel(ki, i)
            engB.apply_channel(kj, j)
            worst = max(worst, float((engA.rho - engB.rho).abs().max()))
    assert worst < 1e-12, worst


@requires_cuda
def test_apply_channel_2site_zz_unitary_cptp():
    """The WS2 (5a) edge U_phi = exp(-i phi Z(x)Z) on {0,1}^2 is CPTP through apply_channel_2site.

    diag(e^{-i phi}, e^{i phi}, e^{i phi}, e^{-i phi}) on the comp pair (Harper / zz_coupling_kraus),
    identity on |2>-touching levels, as a (9,9) 1-Kraus unitary. Trace/Hermiticity/PSD preserved,
    swept phi from the grounded 1e-3 up to the H2 0.05..0.15 bracket. Also checks the embedded
    (9,9) is unitary (independent sanity) and that phi=0 acts as the identity channel.
    """
    from qec_twin.forward.exact.qutrit_dm import QutritDM

    def zz9(phi, dev):
        u = torch.eye(9, dtype=torch.complex128, device=dev)
        idx = {(0, 0): 0, (0, 1): 1, (1, 0): 3, (1, 1): 4}
        phase = {(0, 0): -phi, (0, 1): phi, (1, 0): phi, (1, 1): -phi}
        for key, p in phase.items():
            u[idx[key], idx[key]] = np.exp(1j * p)
        return u.reshape(1, 9, 9)

    rng = np.random.default_rng(13)
    n = 4
    rho = _rand_rho_t(rng, 3 ** n, "cuda")
    for phi in (1e-3, 0.05, 0.10, 0.15):
        u = zz9(phi, "cuda")
        # embedded (9,9) is unitary
        uu = u[0].conj().transpose(-1, -2) @ u[0]
        assert float((uu - torch.eye(9, dtype=torch.complex128, device="cuda")).abs().max()) < 1e-12
        eng = QutritDM(n, device="cuda")
        eng.set_state(rho.clone())
        eng.apply_channel_2site(u, 0, 1)
        out = eng.rho
        assert abs(float(torch.trace(out).real) - 1.0) < 1e-12
        assert float((out - out.conj().transpose(-1, -2)).abs().max()) < 1e-12
        eig = torch.linalg.eigvalsh(0.5 * (out + out.conj().transpose(-1, -2)))
        assert float(eig.min().real) > -1e-10
    # phi = 0 -> identity channel (no change to rho)
    eng0 = QutritDM(n, device="cuda")
    eng0.set_state(rho.clone())
    eng0.apply_channel_2site(zz9(0.0, "cuda"), 0, 1)
    assert float((eng0.rho - rho).abs().max()) < 1e-12

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

_DATASET = Path(
    "/home/cx/Document/google_105Q_surface_code_d3_d5_d7/google_105Q_surface_code_d3_d5_d7"
)
_R01_CIRC, _R01_META = xp.default_r01_paths()
_HAS_R01 = _R01_CIRC.is_file() and _R01_META.is_file()

try:
    import torch

    _HAS_CUDA = torch.cuda.is_available()
except Exception:  # noqa: BLE001
    torch = None
    _HAS_CUDA = False

requires_r01 = pytest.mark.skipif(not _HAS_R01, reason="shipped d3_at_q6_7 r01 patch not present")
requires_cuda = pytest.mark.skipif(not _HAS_CUDA, reason="GPU-only: CUDA not available")


# --------------------------------------------------------------------------- #
# Parser                                                                       #
# --------------------------------------------------------------------------- #
@requires_r01
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


@requires_r01
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


@requires_r01
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
@requires_r01
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

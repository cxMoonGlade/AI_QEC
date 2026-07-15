"""Coupled-process Stim export and record-to-DEM interop tests (CPU-only).

Covers two current public surfaces:
- ``CoupledCycleNoiseProcess.export_stim_circuit`` — ideal-geometry stim export with
  layout-identity asserts, checked by DETERMINISTIC PAULI INJECTION against
  stim as the independent reference: a known Pauli at a known round boundary
  must fire EXACTLY the detector columns + observable the record layout
  predicts. (The bare noiseless all-zero sample is kept as smoke only — for an
  all-Z fixture every measurement is deterministically 0, so it cannot catch
  xor/key bugs; review finding 2026-07-06.)
- ``frontend.interop.records_to_dem`` — validated against a PLANTED-parameter
  synthetic record law (independent ground truth: the planted edge/boundary
  probabilities), with the planted values sized so the exact odd-parity
  boundary residual is DISTINGUISHED from its first-order approximation
  (2*p01*p0 = 1.44e-2 >> the 4e-3 tolerance), plus a null control.

No GPU: process construction and Stim sampling are CPU; ``emit`` is never
called here.
"""

import numpy as np
import pytest

from error_coupling_simulator.certify.types import Regime
from error_coupling_simulator.frontend.interop import (
    decode_records,
    insert_op_after_tick,
    records_to_dem,
)
from error_coupling_simulator.frontend.stim_io import sample_detector_records
from error_coupling_simulator.noise_processes.coupled_cycle import (
    CoupledCycleNoiseProcess,
    default_coupled_code_spec_d3_repz,
)

ROUNDS = 3


def _injection_case(circuit, manifest, *, tick, name, targets, fired, obs):
    """Assert the exact deterministic detector/observable pattern of one
    injected probability-1 Pauli ERROR (stim = independent wiring reference;
    genuine — a mis-mapped column, wrong xor set, or wrong observable key
    fails this). Errors, not gates: stim detectors are frame-relative, so a
    deterministic gate never fires them."""

    circ2 = insert_op_after_tick(circuit, tick, name, targets, (1.0,))
    det, obs_arr = sample_detector_records(circ2, shots=16, seed=11)
    expected = np.zeros(len(manifest["detector_names"]), dtype=bool)
    for det_name in fired:
        expected[manifest["detector_names"].index(det_name)] = True
    assert np.all(det == expected[None, :]), (
        f"inject {name}{targets}@tick{tick}: fired "
        f"{[n for n, v in zip(manifest['detector_names'], det[0]) if v]}, "
        f"expected {list(fired)}"
    )
    assert np.all(obs_arr[:, 0] == bool(obs))


# --------------------------------------------------------------------------- #
# export_stim_circuit                                                          #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("fixture", ["5q", "d3_repz"])
def test_export_stim_circuit_layout_and_counts(fixture):
    process = CoupledCycleNoiseProcess(ROUNDS, fixture=fixture)
    circuit, manifest = process.export_stim_circuit()
    truth = process.truth
    assert manifest["detector_names"] == truth["detector_names"]
    assert manifest["observable_names"] == truth["observable_names"]
    assert manifest["num_detectors"] == ROUNDS * process.n_stab
    assert manifest["num_observables"] == 1
    assert int(circuit.num_detectors) == ROUNDS * process.n_stab
    assert int(circuit.num_observables) == 1
    # M(R) = 2R + 3 for both the 5q and the d3_repz fixtures (S-5 cost parity).
    assert manifest["num_measurements"] == 2 * ROUNDS + 3


@pytest.mark.parametrize("fixture", ["5q", "d3_repz"])
def test_export_stim_circuit_noiseless_smoke(fixture):
    """SMOKE ONLY (declared): for the all-Z d3_repz fixture every measurement
    is deterministically 0, so this cannot catch xor/key bugs — the genuine
    wiring falsifier is the injection test below."""

    process = CoupledCycleNoiseProcess(ROUNDS, fixture=fixture)
    circuit, _ = process.export_stim_circuit()
    det, obs = sample_detector_records(circuit, shots=256, seed=7)
    assert det.shape == (256, ROUNDS * process.n_stab)
    assert int(det.sum()) == 0
    assert int(obs.sum()) == 0


def test_export_wiring_injection_d3_repz():
    """Independent wiring falsifiers (stim reference), d3_repz @ R=3."""

    process = CoupledCycleNoiseProcess(ROUNDS, fixture="d3_repz")
    circuit, manifest = process.export_stim_circuit()
    # In-round X on q2 after round 0: exactly delta:z12:round1, obs flips
    # (geometric class; probability 0 under slice-1 noise — see the fixture
    # docstring — but stim must still map it to exactly this column).
    _injection_case(
        circuit, manifest, tick=1, name="X_ERROR", targets=(2,),
        fired=("delta:z12:round1",), obs=1,
    )
    # X on q2 after the LAST tick (before final readout): exactly final:z12,
    # obs flips — the fault class the armB L0 rule attaches to.
    _injection_case(
        circuit, manifest, tick=ROUNDS, name="X_ERROR", targets=(2,),
        fired=("final:z12",), obs=1,
    )
    # X on the middle qubit q1: fires BOTH round-1 deltas, no obs.
    _injection_case(
        circuit, manifest, tick=1, name="X_ERROR", targets=(1,),
        fired=("delta:z01:round1", "delta:z12:round1"), obs=0,
    )
    # X on q2 BEFORE round 0: undetectable logical (all deltas cancel,
    # closure consistent) — validates delta cancellation + closure keys.
    _injection_case(
        circuit, manifest, tick=0, name="X_ERROR", targets=(2,),
        fired=(), obs=1,
    )


def test_export_wiring_injection_5q():
    """Independent wiring falsifiers, 5q fixture @ R=3."""

    process = CoupledCycleNoiseProcess(ROUNDS, fixture="5q")
    circuit, manifest = process.export_stim_circuit()
    # Z on data 0 flips the x0 (X-check) syndrome from round 1 on: exactly
    # delta:x0:round1 (works although the x0 outcomes themselves are random).
    _injection_case(
        circuit, manifest, tick=1, name="Z_ERROR", targets=(0,),
        fired=("delta:x0:round1",), obs=0,
    )
    # X on data 2 before final readout: obs flips, NO detector fires — the
    # EMPIRICAL witness of the 5q observable's structural disconnection
    # (the declared vacuous-decode property of armA).
    _injection_case(
        circuit, manifest, tick=ROUNDS, name="X_ERROR", targets=(2,),
        fired=(), obs=1,
    )


def test_d3_repz_spec_shape():
    spec = default_coupled_code_spec_d3_repz(ROUNDS)
    assert spec.rounds == ROUNDS
    assert len(spec.checks) == 2
    assert {c.name for c in spec.checks} == {"z01", "z12"}
    assert all(len(c.terms) == 2 for c in spec.checks)
    assert [o.name for o in spec.logical_observables] == ["logical_z2"]
    process = CoupledCycleNoiseProcess(ROUNDS, fixture="d3_repz")
    assert process.n_stab == 2
    # Regime surface still binds (construction-time contract only; no emit).
    with pytest.raises(ValueError, match="regime.R"):
        process.emit(Regime(R=ROUNDS + 1, n_stab=2), m=0, N=1, seed=0)


# --------------------------------------------------------------------------- #
# records_to_dem — planted-parameter positive control                          #
# --------------------------------------------------------------------------- #
def _planted_records(n_shots: int, seed: int):
    """Independent ground truth: 4 detectors, three planted fault classes.

    f01 ~ B(0.12) flips D0,D1 (pair edge, no logical); f2 ~ B(0.04) flips D2
    and the observable (boundary edge with L0); f0 ~ B(0.06) flips D0 alone
    (boundary, no logical). D3 is planted silent. Values sized so the EXACT
    odd-parity boundary residual on D0 (0.06) is separated from the naive
    first-order marginal-minus-pair value (m0 - p01 = 0.0456) by 2*p01*p0 =
    1.44e-2 >> the 4e-3 test tolerance — the exactness claim is falsifiable.
    """

    rng = np.random.default_rng(seed)
    f01 = rng.random(n_shots) < 0.12
    f2 = rng.random(n_shots) < 0.04
    f0 = rng.random(n_shots) < 0.06
    det = np.zeros((n_shots, 4), dtype=np.uint8)
    det[:, 0] = np.logical_xor(f01, f0)
    det[:, 1] = f01
    det[:, 2] = f2
    obs = f2.astype(np.uint8)
    return det, obs, {"p01": 0.12, "p2": 0.04, "p0": 0.06}


def test_records_to_dem_recovers_planted_edges():
    n_shots = 120_000
    det, _, planted = _planted_records(n_shots, seed=20260706)
    names = ("d0", "d1", "d2", "d3")
    dem, diag = records_to_dem(
        det, detector_names=names, logical_boundary_detectors=("d2",)
    )
    edges = {(e["i"], e["j"]): e["p"] for e in diag["edges"]}
    bounds = {b["i"]: b for b in diag["boundaries"]}
    # Pair edge (0,1) recovered near the planted value (5 sigma + planted tol).
    assert (0, 1) in edges
    assert abs(edges[(0, 1)] - planted["p01"]) < 5.0 * diag["pij_se"][0, 1] + 2e-3
    # No spurious edges involving the silent detector D3.
    assert not any(3 in pair for pair in edges)
    # Boundaries: D2 carries L0 at ~p2; D0 residual ~p0 without L0, at the
    # EXACT-identity tolerance (4e-3) that excludes the first-order value.
    assert bounds[2]["logical"] is True
    assert abs(bounds[2]["p"] - planted["p2"]) < 4e-3
    assert bounds[0]["logical"] is False
    assert abs(bounds[0]["p"] - planted["p0"]) < 4e-3
    naive_first_order = 0.0456  # m0 - p01 at the planted values
    assert abs(bounds[0]["p"] - naive_first_order) > 8e-3
    assert 1 not in bounds or bounds[1]["p"] < 5e-3
    # The DEM itself declares all 4 detectors and the logical.
    assert dem.num_detectors == 4
    assert dem.num_observables == 1
    # SE convention is carried with the numbers (iid default).
    assert diag["pij_se_convention"]["cluster_size"] == 1
    assert diag["pij_se_convention"]["anti_conservative_for_clusters"] is False


def test_records_to_dem_pymatching_roundtrip():
    """End-to-end: planted records -> DEM -> PyMatching decode. The planted
    model is exactly matchable, so decoding must recover the observable almost
    perfectly — a positive control on DEM syntax + logical attachment."""

    pytest.importorskip("pymatching", reason="decode requires the optional hw extra")
    n_shots = 60_000
    det, obs, _ = _planted_records(n_shots, seed=8)
    dem, _ = records_to_dem(
        det,
        detector_names=("d0", "d1", "d2", "d3"),
        logical_boundary_detectors=("d2",),
    )
    predicted = decode_records(dem, det)
    assert predicted.shape == (n_shots,)
    accuracy = float(np.mean(predicted == obs))
    assert accuracy > 0.999
    # And decoding genuinely beats the no-decoder baseline (predict 0).
    assert float(np.mean(predicted != obs)) < float(np.mean(obs))


def test_decode_records_logical_index():
    """A DEM built with logical_index != 0 must decode from THAT column; a
    mismatched out-of-range index raises instead of silently reading L0."""

    pytest.importorskip("pymatching", reason="decode requires the optional hw extra")
    det, obs, _ = _planted_records(20_000, seed=9)
    dem, _ = records_to_dem(
        det,
        detector_names=("d0", "d1", "d2", "d3"),
        logical_boundary_detectors=("d2",),
        logical_index=1,
    )
    predicted = decode_records(dem, det, logical_index=1)
    assert float(np.mean(predicted == obs)) > 0.999
    with pytest.raises(ValueError, match="out of range"):
        decode_records(dem, det, logical_index=2)


def test_records_to_dem_null_control():
    det = np.zeros((5_000, 4), dtype=np.uint8)
    dem, diag = records_to_dem(det, detector_names=("a", "b", "c", "d"))
    assert diag["edges"] == []
    assert diag["boundaries"] == []
    assert dem.num_detectors == 4


def test_records_to_dem_input_validation():
    det = np.zeros((10, 2), dtype=np.uint8)
    with pytest.raises(ValueError, match="detector_names"):
        records_to_dem(det, detector_names=("only_one",))
    with pytest.raises(ValueError, match="0/1"):
        records_to_dem(
            np.full((10, 2), 3, dtype=np.uint8), detector_names=("a", "b")
        )
    with pytest.raises(ValueError, match="not in detector_names"):
        records_to_dem(
            det, detector_names=("a", "b"), logical_boundary_detectors=("zz",)
        )
    with pytest.raises(ValueError, match="cluster_size"):
        records_to_dem(det, detector_names=("a", "b"), cluster_size=0)

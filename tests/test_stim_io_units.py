"""Stage-D batch ``stim_io`` -- per-unit L0+L1+L2 coverage of
``error_coupling_simulator.frontend.stim_io`` (7 CPU-pure public units: the seven
module-level functions ``circuit_to_stim`` / ``load_stim_circuit`` / ``write_stim_circuit`` /
``write_detector_error_model`` / ``detector_error_model`` / ``counts`` /
``sample_detector_records``; the frozen dataclass ``StimCounts`` has NO methods so it
contributes no units; the module imports NEITHER torch NOR quimb -- ``stim`` is a lazy import
inside ``circuit_to_stim`` / ``load_stim_circuit`` -- so out_of_scope is empty).

Full-coverage program (docs/SIMULATOR.md SS12.3/12.4;
work-list docs/SIMULATOR.md D23).
``frontend/stim_io.py`` owns the Stim adapters that move between the key-based ``CircuitIR``
and concrete ``stim.Circuit`` / ``stim.DetectorErrorModel`` artifacts (build / load / write /
DEM / counts / sample).

L2 DISCIPLINE (100% coverage != discrimination). The emitted stim circuit is pinned OP-BY-OP
against an INDEPENDENT hand-built ``stim.Circuit`` (built from stim primitives, NOT via
``circuit_to_stim``); every count is pinned vs a direct read off the ``stim.Circuit``; the
DEM is pinned vs ``circuit.detector_error_model(...)`` with the True-vs-False split made
load-bearing by a surface-code circuit whose two DEMs differ; the sampler's det/obs slice is
pinned on a deterministic (X_ERROR(1.0)) circuit; and every reachable guard of the private
``_qubit_coords_from_metadata`` is tripped through a real ``CircuitIR.metadata`` route with the
EXACT message via ``assert_raises_exact``. The two DEFENSIVE raises in ``_record_targets`` are
structurally UNREACHABLE via a valid CircuitIR (its ``__post_init__`` already rejects an
unmeasured record key, and a key's measurement index is always strictly < ``measurement_count``
so the offset is always negative) -- their message mutants are equivalent (see the registry
``_comment``).
"""
from __future__ import annotations

import dataclasses
import types
from pathlib import Path

import numpy as np
import pytest
import stim
from hypothesis import given, settings
from hypothesis import strategies as st

from _support.faithfulness import assert_discriminates, assert_pins, assert_raises_exact

from error_coupling_simulator.frontend.circuit_ir import (
    CircuitBuilder,
    CircuitIR,
    DetectorDef,
)
from error_coupling_simulator.frontend.stim_io import (
    StimCounts,
    circuit_to_stim,
    counts,
    detector_error_model,
    load_stim_circuit,
    sample_detector_records,
    write_detector_error_model,
    write_stim_circuit,
)


def _rec(i: int):
    return stim.target_rec(i)


# --------------------------------------------------------------------------- #
# INDEPENDENT input builders + hand-built expected stim circuits.             #
# --------------------------------------------------------------------------- #
def _ir_main() -> CircuitIR:
    """A curated 3-qubit round-trippable CircuitIR exercising ALL FIVE step kinds in order:
    H0 (GateOp) -> CX(0,1) (GateOp) -> TICK (Tick) -> M(0,1) keys m0,m1 (MeasureOp) ->
    DETECTOR d0 = m0^m1 (DetectorDef) -> OBSERVABLE L0 = m0 (ObservableDef). Metadata supplies
    qubit_coords for qubits 0,1 but NOT 2, so the QUBIT_COORDS default arc (2 -> [2.0]) fires.

    (NB: canonical_circuit_ir() is NOT usable here -- its idle(duration_ns=50) emits a stim
    `I` gate with a parens argument stim rejects; D20 caveat.)"""
    b = CircuitBuilder(num_qubits=3,
                       metadata={"qubit_coords": {0: [0.0, 1.0], 1: [1.0, 2.0]}})
    b.h(0)
    b.cx((0, 1))
    b.tick()
    b.measure((0, 1), key=("m0", "m1"))
    b.detector("d0", xor=("m0", "m1"), coords=(3.0, 4.0))  # non-empty coords are load-bearing
    b.observable("L0", xor=("m0",), index=0)
    return b.build()


def _expected_main() -> stim.Circuit:
    """INDEPENDENT hand-built expectation for circuit_to_stim(_ir_main()): QUBIT_COORDS for 3
    qubits (2 from metadata, 1 default float(q)), the gates, TICK, M, then rec-relative DETECTOR
    (m0->rec[-2], m1->rec[-1]) and OBSERVABLE_INCLUDE (m0->rec[-2], index 0.0)."""
    c = stim.Circuit()
    c.append("QUBIT_COORDS", [0], [0.0, 1.0])
    c.append("QUBIT_COORDS", [1], [1.0, 2.0])
    c.append("QUBIT_COORDS", [2], [2.0])
    c.append("H", [0])
    c.append("CX", [0, 1])
    c.append("TICK")
    c.append("M", [0, 1])
    c.append("DETECTOR", [_rec(-2), _rec(-1)], [3.0, 4.0])
    c.append("OBSERVABLE_INCLUDE", [_rec(-2)], 0.0)
    return c


_EXPECTED_MAIN_OPS = [
    "QUBIT_COORDS", "QUBIT_COORDS", "QUBIT_COORDS", "H", "CX", "TICK",
    "M", "DETECTOR", "OBSERVABLE_INCLUDE",
]


def _distinct_count_circuit() -> stim.Circuit:
    """A stim circuit whose four counts are ALL DISTINCT: 4 qubits, 3 measurements, 2 detectors,
    1 observable -- so a counts() field<->property mis-mapping is caught."""
    c = stim.Circuit()
    for q in range(4):
        c.append("QUBIT_COORDS", [q], [float(q)])
    c.append("M", [0, 1, 2])                       # 3 measurements
    c.append("DETECTOR", [_rec(-1)])
    c.append("DETECTOR", [_rec(-2)])               # 2 detectors
    c.append("OBSERVABLE_INCLUDE", [_rec(-3)], 0)  # 1 observable
    return c


def _deterministic_det_obs_circuit() -> stim.Circuit:
    """A DETERMINISTIC circuit (X_ERROR(1.0) => qubit 0 certainly flips): 1 detector (= m0 = 1,
    fires True) + 1 observable (= m1 = 0, False). The X_ERROR keeps the detector legitimately
    non-structural (no deterministic-detector complaint) while pinning det=True / obs=False."""
    c = stim.Circuit()
    c.append("R", [0, 1])
    c.append("X_ERROR", [0], 1.0)                  # qubit 0 certainly flipped -> m0 = 1
    c.append("M", [0, 1])                          # m0 = 1, m1 = 0
    c.append("DETECTOR", [_rec(-2)])               # = m0 = 1 -> True
    c.append("OBSERVABLE_INCLUDE", [_rec(-1)], 0)  # = m1 = 0 -> False
    return c


def _surface_code_circuit() -> stim.Circuit:
    """A generated rotated surface-code memory circuit with depolarizing noise -- its Y-type
    errors flip >2 detectors, so decompose_errors=True and =False give DIFFERENT DEMs."""
    return stim.Circuit.generated(
        "surface_code:rotated_memory_z", distance=3, rounds=1,
        after_clifford_depolarization=0.01)


# =========================================================================== #
# circuit_to_stim                                                              #
# =========================================================================== #
def test_L0_circuit_to_stim_op_by_op_matches_independent_expectation():
    emitted = circuit_to_stim(_ir_main())
    expected = _expected_main()
    # full-circuit equality (pins targets + gate args + rec offsets exactly) ...
    assert emitted == expected
    # ... a readable str diff on failure ...
    assert str(emitted) == str(expected)
    # ... and the exact op-name sequence (INDEPENDENT hardcoded list; kills a mutated
    # "QUBIT_COORDS"/"DETECTOR"/"OBSERVABLE_INCLUDE"/"TICK" literal -> stim would reject it).
    assert [inst.name for inst in emitted] == _EXPECTED_MAIN_OPS

    def prop(c):
        assert c == expected

    # a wrong-rec-offset variant must fail the pin (the += / offset arithmetic has teeth).
    wrong = _expected_main()
    wrong = stim.Circuit(str(wrong).replace("rec[-2] rec[-1]", "rec[-1] rec[-2]"))
    assert_discriminates(prop, emitted, wrong, label="circuit_to_stim op-by-op")


def test_L0_circuit_to_stim_qubit_coords_default_and_no_metadata():
    # a 2-qubit circuit with NO qubit_coords metadata -> BOTH qubits take the default [float(q)]
    # (the _qubit_coords_from_metadata raw={} default arc + the .get default arc), plus the
    # X (GateOp) / M (MeasureOp) / OBSERVABLE (ObservableDef) routes with no TICK/DETECTOR.
    b = CircuitBuilder(num_qubits=2)
    b.x(0)
    b.measure((0,), key="m0")
    b.observable("L0", xor=("m0",), index=0)
    emitted = circuit_to_stim(b.build())
    expected = stim.Circuit()
    expected.append("QUBIT_COORDS", [0], [0.0])
    expected.append("QUBIT_COORDS", [1], [1.0])
    expected.append("X", [0])
    expected.append("M", [0])
    expected.append("OBSERVABLE_INCLUDE", [_rec(-1)], 0.0)
    assert emitted == expected
    assert [inst.name for inst in emitted] == [
        "QUBIT_COORDS", "QUBIT_COORDS", "X", "M", "OBSERVABLE_INCLUDE"]


def test_L0_circuit_to_stim_qubit_coords_non_mapping_raises_exact():
    # metadata['qubit_coords'] present but NOT a dict (a list) -> the mapping guard fires.
    ir = CircuitIR(num_qubits=2, steps=(), metadata={"qubit_coords": [1, 2]})
    assert_raises_exact(
        ValueError,
        "CircuitIR.metadata['qubit_coords'] must be a mapping if present",
        lambda: circuit_to_stim(ir),
        label="qubit_coords non-mapping")


def test_L0_circuit_to_stim_qubit_coords_key_out_of_range_raises_exact():
    # q == num_qubits: the `>=` BOUNDARY (kills `>=`->`>`, which would let q==num_qubits pass) and
    # the second `or` operand.
    ir_hi = CircuitIR(num_qubits=2, steps=(), metadata={"qubit_coords": {2: [0.0]}})
    assert_raises_exact(
        ValueError,
        "qubit_coords key 2 outside [0, 2)",
        lambda: circuit_to_stim(ir_hi),
        label="qubit_coords key at num_qubits boundary")
    # ... and q < 0 (first `or` operand). Both operands independently trip the raise, so a
    # `or`->`and` mutant (which would suppress the raise on each single-operand case) is killed.
    ir_lo = CircuitIR(num_qubits=2, steps=(), metadata={"qubit_coords": {-1: [0.0]}})
    assert_raises_exact(
        ValueError,
        "qubit_coords key -1 outside [0, 2)",
        lambda: circuit_to_stim(ir_lo),
        label="qubit_coords key negative")


def test_L0_circuit_to_stim_qubit_coords_empty_raises_exact():
    # a present-but-EMPTY coords list -> the empty-coords guard fires.
    ir = CircuitIR(num_qubits=2, steps=(), metadata={"qubit_coords": {0: []}})
    assert_raises_exact(
        ValueError,
        "qubit_coords for qubit 0 must not be empty",
        lambda: circuit_to_stim(ir),
        label="qubit_coords empty")


def test_L0_circuit_to_stim_forwards_gate_args_to_stim():
    # a GateOp with args (idle I with a duration) forwards list(step.args)=[50.0] to stim, which
    # REJECTS an `I` gate with a parens argument. This pins that gate args are actually forwarded:
    # a mutant that passes None / drops the args would emit an argless `I` -> NO raise. (Valid
    # non-idle gates carry empty args, so this is the one route that makes the args load-bearing.)
    b = CircuitBuilder(num_qubits=1)
    b.idle((0,), duration_ns=50.0)
    ir = b.build()
    with pytest.raises(ValueError):
        circuit_to_stim(ir)


def test_L0_circuit_to_stim_unknown_step_type_raises_exact():
    # the exhaustive `else` guard (a step that is none of Tick/GateOp/MeasureOp/DetectorDef/
    # ObservableDef). A valid CircuitIR cannot carry one (its __post_init__ rejects unknown step
    # types), so it is PROBED through the public entry with a duck-typed fake circuit whose one
    # step is a bare object(); type(object()) has the stable repr <class 'object'>. This trips the
    # defensive TypeError with the EXACT message (kills the None-message + type(None) mutants).
    fake = types.SimpleNamespace(num_qubits=1, metadata={}, steps=(object(),))
    assert_raises_exact(
        TypeError,
        "unknown circuit step <class 'object'>",
        lambda: circuit_to_stim(fake),
        label="unknown circuit step guard")


def test_L0_circuit_to_stim_record_key_not_measured_raises_exact():
    # _record_targets' unmeasured-key guard. A valid CircuitIR cannot reach it (__post_init__ via
    # _require_known_keys rejects a DetectorDef referencing an unmeasured key), so it is PROBED via
    # a duck-typed fake circuit whose DetectorDef references a key never measured -> the guard trips
    # with the EXACT message (kills the None-message mutant on the raise).
    fake = types.SimpleNamespace(
        num_qubits=1, metadata={}, steps=(DetectorDef("d0", ("nope",)),))
    assert_raises_exact(
        ValueError,
        "record key 'nope' was not measured before this declaration",
        lambda: circuit_to_stim(fake),
        label="record key unmeasured guard")


# =========================================================================== #
# counts / StimCounts                                                          #
# =========================================================================== #
def test_L0_counts_pins_all_four_distinct_counts():
    c = _distinct_count_circuit()
    sc = counts(c)
    assert isinstance(sc, StimCounts)
    # INDEPENDENT reads straight off the stim.Circuit (NOT via StimCounts).
    assert sc.num_detectors == int(c.num_detectors) == 2
    assert sc.num_observables == int(c.num_observables) == 1
    assert sc.num_measurements == int(c.num_measurements) == 3
    assert sc.num_qubits == int(c.num_qubits) == 4

    def prop(x):
        assert (x.num_detectors, x.num_observables, x.num_measurements, x.num_qubits) == (
            2, 1, 3, 4)

    # det<->obs swapped: because all four counts differ, any field/property mis-mapping fails.
    wrong = StimCounts(num_detectors=1, num_observables=2, num_measurements=3, num_qubits=4)
    assert_discriminates(prop, sc, wrong, label="counts field mapping")


def test_L0_stimcounts_is_frozen_dataclass():
    sc = StimCounts(num_detectors=1, num_observables=2, num_measurements=3, num_qubits=4)
    assert (sc.num_detectors, sc.num_observables, sc.num_measurements, sc.num_qubits) == (
        1, 2, 3, 4)
    # frozen=True -> assignment raises FrozenInstanceError (kills a frozen=True->False mutant).
    with pytest.raises(dataclasses.FrozenInstanceError):
        sc.num_qubits = 9  # type: ignore[misc]


# =========================================================================== #
# detector_error_model                                                        #
# =========================================================================== #
def test_L0_detector_error_model_default_true_and_explicit_false():
    c = _surface_code_circuit()
    dem_true_ref = c.detector_error_model(decompose_errors=True)    # INDEPENDENT stim calls
    dem_false_ref = c.detector_error_model(decompose_errors=False)
    # this surface-code circuit's decomposition is load-bearing: the two DEMs DIFFER.
    assert dem_true_ref != dem_false_ref
    # default routes to decompose_errors=True (kills the default True->False mutant: under it
    # the default call would equal dem_false_ref != dem_true_ref).
    assert detector_error_model(c) == dem_true_ref
    # an explicit False is threaded through (kills a `decompose_errors=decompose_errors`->True).
    assert detector_error_model(c, decompose_errors=False) == dem_false_ref
    # structural pin: the DEM sees the circuit's detectors.
    assert detector_error_model(c).num_detectors == int(c.num_detectors)

    def prop(dem):
        assert dem == dem_true_ref

    assert_discriminates(prop, detector_error_model(c),
                         detector_error_model(c, decompose_errors=False),
                         label="detector_error_model decompose default")


# =========================================================================== #
# write_stim_circuit / load_stim_circuit                                       #
# =========================================================================== #
def test_L0_write_and_load_stim_circuit_roundtrip(tmp_path):
    c = circuit_to_stim(_ir_main())
    path = tmp_path / "circ.stim"
    ret = write_stim_circuit(c, path)
    # returns the Path; the file exists; its text is exactly str(circuit) (INDEPENDENT of stim_io).
    assert ret == path and isinstance(ret, Path)
    assert path.exists()
    assert path.read_text() == str(c)
    # write->load reconstructs an EQUAL circuit (the real round-trip contract) ...
    assert load_stim_circuit(path) == c
    # ... and load_stim_circuit accepts a str path too.
    assert load_stim_circuit(str(path)) == c
    # a str path input still returns a Path (kills a removed Path(path) coercion).
    ret2 = write_stim_circuit(c, str(tmp_path / "circ2.stim"))
    assert isinstance(ret2, Path)
    assert load_stim_circuit(ret2) == c


def test_L0_write_stim_circuit_content_discriminates(tmp_path):
    c = circuit_to_stim(_ir_main())
    path = write_stim_circuit(c, tmp_path / "c.stim")

    def prop(loaded):
        assert loaded == c

    # a DIFFERENT circuit loaded from a different file must fail the pin -> the round-trip bites.
    other = stim.Circuit()
    other.append("H", [0])
    other_path = write_stim_circuit(other, tmp_path / "other.stim")
    assert_discriminates(prop, load_stim_circuit(path), load_stim_circuit(other_path),
                         label="write/load round-trip")


# =========================================================================== #
# write_detector_error_model                                                   #
# =========================================================================== #
def test_L0_write_detector_error_model_roundtrip(tmp_path):
    c = _surface_code_circuit()
    dem = detector_error_model(c)
    path = tmp_path / "model.dem"
    ret = write_detector_error_model(dem, path)
    assert ret == path and isinstance(ret, Path)
    assert path.exists()
    assert path.read_text() == str(dem)
    # round-trip via an INDEPENDENT stim loader.
    assert stim.DetectorErrorModel.from_file(str(path)) == dem
    # a str path input returns a Path (kills a removed Path(path) coercion).
    ret2 = write_detector_error_model(dem, str(tmp_path / "m2.dem"))
    assert isinstance(ret2, Path)
    assert stim.DetectorErrorModel.from_file(str(ret2)) == dem


# =========================================================================== #
# sample_detector_records                                                      #
# =========================================================================== #
def test_L0_sample_detector_records_deterministic_split():
    c = _deterministic_det_obs_circuit()   # 1 detector (True), 1 observable (False)
    det, obs = sample_detector_records(c, shots=5, seed=1)
    # shapes: det=(shots, n_det), obs=(shots, n_obs) -- the slice split is load-bearing.
    assert det.shape == (5, 1) and obs.shape == (5, 1)
    assert det.dtype == np.bool_ and obs.dtype == np.bool_
    # det all True (the detector fires), obs all False -- a swapped/offset slice would flip these.
    assert det.all() and not obs.any()
    # seed=None (the default arg) on the deterministic circuit gives the SAME pinned values.
    det0, obs0 = sample_detector_records(c, shots=3)
    assert det0.shape == (3, 1) and det0.all() and not obs0.any()

    def prop(pair):
        d, o = pair
        assert d.all() and not o.any()

    # sabotaged: det<->obs swapped must fail the split property -> teeth on the slice.
    assert_discriminates(prop, (det, obs), (obs, det),
                         label="sample_detector_records det/obs split")


def test_L0_sample_detector_records_seed_reproducible_and_float_shots():
    # a NOISY circuit: same seed => identical samples (kills a dropped seed=seed).
    cn = stim.Circuit()
    cn.append("R", [0])
    cn.append("X_ERROR", [0], 0.5)
    cn.append("M", [0])
    cn.append("DETECTOR", [_rec(-1)])
    a1, o1 = sample_detector_records(cn, shots=64, seed=7)
    a2, o2 = sample_detector_records(cn, shots=64, seed=7)
    assert np.array_equal(a1, a2) and np.array_equal(o1, o2)
    assert a1.shape == (64, 1) and o1.shape == (64, 0)
    # the p=0.5 noise is a genuine mixture at seed=7 (not a degenerate all-True/all-False draw),
    # so the reproducibility pin is over real randomness, not a constant.
    assert a1.any() and not a1.all()
    # float shots is accepted via int(shots).
    det, _ = sample_detector_records(cn, shots=8.0, seed=3)
    assert det.shape == (8, 1)


# =========================================================================== #
# L1 PROPERTIES (Hypothesis)                                                    #
# =========================================================================== #
@settings(max_examples=120, deadline=None)
@given(k=st.integers(1, 6), nobs=st.integers(0, 3))
def test_L1_counts_reads_structural_counts(k, nobs):
    c = stim.Circuit()
    for q in range(k):
        c.append("QUBIT_COORDS", [q], [float(q)])
    c.append("M", list(range(k)))                        # k measurements
    for i in range(k):
        c.append("DETECTOR", [_rec(-(i + 1))])           # k detectors
    for j in range(nobs):
        c.append("OBSERVABLE_INCLUDE", [_rec(-1)], j)    # nobs observables (indices 0..nobs-1)
    sc = counts(c)
    # INDEPENDENT recompute: counts read straight off the stim.Circuit's own properties.
    assert (sc.num_measurements, sc.num_detectors, sc.num_observables, sc.num_qubits) == (
        int(c.num_measurements), int(c.num_detectors), int(c.num_observables),
        int(c.num_qubits))
    assert (sc.num_measurements, sc.num_detectors, sc.num_observables, sc.num_qubits) == (
        k, k, nobs, k)


@settings(max_examples=100, deadline=None)
@given(k=st.integers(1, 5))
def test_L1_circuit_to_stim_counts_roundtrip(k):
    b = CircuitBuilder(num_qubits=k)
    keys = tuple(f"m{i}" for i in range(k))
    b.measure(tuple(range(k)), key=keys)
    for i, key in enumerate(keys):
        b.detector(f"d{i}", xor=(key,))
    b.observable("L0", xor=(keys[0],), index=0)
    sc = counts(circuit_to_stim(b.build()))
    # the emitted stim circuit carries exactly the IR's k measurements/detectors + 1 observable.
    assert_pins([sc.num_measurements, sc.num_detectors, sc.num_observables, sc.num_qubits],
                [k, k, 1, k], label="circuit_to_stim counts round-trip")


@settings(max_examples=80, deadline=None)
@given(shots=st.integers(0, 32), seed=st.integers(0, 2 ** 16 - 1))
def test_L1_sample_shapes_and_deterministic_values(shots, seed):
    c = _deterministic_det_obs_circuit()
    det, obs = sample_detector_records(c, shots=shots, seed=seed)
    # shapes always (shots, n_det) / (shots, n_obs) (INDEPENDENT recompute from stim counts).
    assert det.shape == (shots, int(c.num_detectors))
    assert obs.shape == (shots, int(c.num_observables))
    assert det.dtype == np.bool_ and obs.dtype == np.bool_
    # deterministic circuit: det all True, obs all False regardless of seed/shots.
    if shots > 0:
        assert det.all() and not obs.any()

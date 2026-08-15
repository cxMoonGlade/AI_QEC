"""Public behavior tests for the simulator's optional PyMatching decoder port."""

from __future__ import annotations

import sys

import numpy as np
import pytest
import stim

from error_coupling_simulator.frontend import b8_io, decoder
from error_coupling_simulator.frontend.circuit_ir import CircuitBuilder
from error_coupling_simulator.frontend.simulator import Simulator


def test_decode_dem_accepts_bool_and_unambiguous_packed_detector_records() -> None:
    """Both supported detector layouts decode identically at upstream defaults."""

    pytest.importorskip("pymatching", reason="decoder requires the optional hw extra")
    dem = stim.DetectorErrorModel(
        "error(0.1) D0\n"
        "error(0.1) D1\n"
        "error(0.1) D2 L0"
    )
    detectors = np.array(
        [
            [0, 0, 0],
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [1, 1, 1],
        ],
        dtype=np.bool_,
    )
    expected = np.array([[0], [0], [0], [1], [1]], dtype=np.uint8)

    unpacked_predictions = decoder.decode_dem(dem, detectors)
    packed_predictions = decoder.decode_dem(dem, b8_io.pack_bits(detectors))

    assert unpacked_predictions.dtype == np.uint8
    assert unpacked_predictions.shape == (5, 1)
    assert np.array_equal(unpacked_predictions, expected)
    assert np.array_equal(packed_predictions, expected)


def test_pymatching_provenance_keeps_the_registered_pin_and_wheel_identity() -> None:
    """The optional decoder reports the frozen external-wheel provenance."""

    pytest.importorskip("pymatching", reason="provenance pin requires the optional hw extra")
    provenance = decoder.pymatching_provenance()

    assert provenance["pinned_version"] == "2.4.0"
    assert provenance["installed_version"] == "2.4.0"
    assert provenance["version_match"] is True
    assert provenance["wheel_filename"] == (
        "pymatching-2.4.0-cp312-cp312-manylinux_2_27_x86_64."
        "manylinux_2_28_x86_64.whl"
    )
    assert provenance["wheel_sha256"] == (
        "15e6d73153713a8f383f44ba4497d478fb4c4d765fbdd30f9fc1e1d47af75760"
    )
    assert provenance["installed_binary_path"].endswith(".so")
    assert len(provenance["installed_binary_sha256"]) == 64
    assert provenance["provenance_complete"] is True


def test_simulator_routes_predictions_through_the_package_decoder_port(
    monkeypatch,
    tmp_path,
) -> None:
    """The product facade consumes the package-local decoder implementation."""

    builder = CircuitBuilder(num_qubits=1)
    builder.measure(0, key="m0")
    builder.detector("d0", xor=["m0"])
    builder.observable("logical0", xor=["m0"], index=0)

    def sentinel_decode(_dem, detectors):
        return np.ones((np.asarray(detectors).shape[0], 1), dtype=np.uint8)

    monkeypatch.setattr(decoder, "decode_dem", sentinel_decode)
    result = Simulator(builder.build()).run(
        shots=5,
        out_dir=tmp_path,
        seed=7,
        decoder="pymatching",
    )
    predictions = b8_io.unpack_bits(
        b8_io.read_b8(result.paths.obs_flips_predicted, 1),
        1,
    )
    assert predictions.shape == (5, 1)
    assert predictions.all()


def test_decode_dem_rejects_ambiguous_single_detector_uint8_records() -> None:
    """Width-one uint8 cannot silently mean both packed and unpacked records."""

    pytest.importorskip("pymatching", reason="decoder requires the optional hw extra")
    dem = stim.DetectorErrorModel("error(0.1) D0 L0")
    ambiguous = np.array([[0], [1]], dtype=np.uint8)

    with pytest.raises(ValueError, match="ambiguous uint8 dets"):
        decoder.decode_dem(dem, ambiguous)


def test_decode_dem_reports_the_missing_optional_hw_extra(monkeypatch) -> None:
    """A core-only install fails with an actionable dependency boundary."""

    monkeypatch.setitem(sys.modules, "pymatching", None)
    dem = stim.DetectorErrorModel("error(0.1) D0 L0")
    detectors = np.zeros((1, 1), dtype=np.bool_)

    with pytest.raises(
        ImportError,
        match=r"optional 'hw' extra: install error-coupling-simulator\[hw\]",
    ):
        decoder.decode_dem(dem, detectors)

from __future__ import annotations

import numpy as np
import pytest


def test_packed_shot_batch_exposes_temporal_detector_events() -> None:
    from error_coupling_simulator.carrier.records import PackedShotBatch

    raw_syndromes = np.array(
        [
            [1, 0, 1, 1, 0, 1],
            [0, 1, 1, 1, 1, 0],
        ],
        dtype=np.uint8,
    )
    logical_flips = np.array([1, 0], dtype=np.uint8)

    shots = PackedShotBatch.from_raw_syndromes(
        raw_syndromes,
        logical_flips,
        rounds=3,
        num_stabilizers=2,
        provenance={"backend": "unit-test"},
    )
    record = shots.to_record_batch()

    expected_detectors = np.array(
        [
            [1, 0, 0, 1, 1, 0],
            [0, 1, 1, 0, 0, 1],
        ],
        dtype=np.uint8,
    )
    np.testing.assert_array_equal(record.det, expected_detectors)
    np.testing.assert_array_equal(record.obs, logical_flips)
    np.testing.assert_array_equal(shots.to_raw_syndrome_obs()["syndrome"], raw_syndromes)
    np.testing.assert_array_equal(
        shots.shots,
        np.array([[0x2D, 1], [0x1E, 0]], dtype=np.uint8),
    )
    np.testing.assert_array_equal(shots.to_det_obs()["det"], expected_detectors)
    assert record.provenance["record_semantics"] == "temporal_detector_events"
    assert record.provenance["backend"] == "unit-test"


def test_record_batch_rejects_evaluator_only_truth_in_provenance() -> None:
    from error_coupling_simulator.carrier.records import RecordBatch

    with pytest.raises(ValueError, match="evaluator-only"):
        RecordBatch(
            det=np.zeros((1, 1), dtype=np.uint8),
            obs=np.zeros((1,), dtype=np.uint8),
            provenance={"nested": {"truth": {"source_timeline": [0.0]}}},
        )

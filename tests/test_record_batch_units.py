from __future__ import annotations

import numpy as np
import pytest


_PACKED_FORMAT = "error_coupling_simulator.carrier.packed_shots.v1"
_PACKED_LAYOUT = "round_major_lsb_syndrome_then_logical_u8"


def _packed_header(
    *, n_shots: int = 1, rounds: int = 1, num_stabilizers: int = 1,
) -> dict[str, object]:
    syndrome_bits = rounds * num_stabilizers
    return {
        "format": _PACKED_FORMAT,
        "n_stab": num_stabilizers,
        "R": rounds,
        "N": n_shots,
        "syndrome_bits_per_shot": syndrome_bits,
        "out_stride_bytes": (syndrome_bits + 7) // 8 + 1,
        "syndrome_layout": _PACKED_LAYOUT,
        "detector_initial_prior": "all_zero",
    }


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
    assert record.det.flags.c_contiguous
    assert record.obs.flags.c_contiguous
    assert not record.det.flags.writeable
    assert not record.obs.flags.writeable
    assert shots.shots is not None
    assert shots.shots.flags.c_contiguous
    assert not shots.shots.flags.writeable


def test_record_batch_rejects_evaluator_only_truth_in_provenance() -> None:
    from error_coupling_simulator.carrier.records import RecordBatch

    with pytest.raises(ValueError, match="evaluator-only"):
        RecordBatch(
            det=np.zeros((1, 1), dtype=np.uint8),
            obs=np.zeros((1,), dtype=np.uint8),
            provenance={"nested": {"truth": {"source_timeline": [0.0]}}},
        )


@pytest.mark.parametrize("field", ["det", "obs"])
@pytest.mark.parametrize("bad", [256, -256, 0.0, 0.9, np.nan, np.inf, -np.inf])
def test_record_batch_rejects_invalid_original_values_before_uint8_narrowing(
    field: str, bad: float,
) -> None:
    from error_coupling_simulator.carrier.records import RecordBatch

    det = np.zeros((1, 1), dtype=np.uint8)
    obs = np.zeros((1,), dtype=np.uint8)
    if field == "det":
        det = np.array([[bad]])
    else:
        obs = np.array([bad])
    with pytest.raises((TypeError, ValueError), match="integer|0/1"):
        RecordBatch(det=det, obs=obs)


def test_record_batch_copies_valid_inputs_to_read_only_contiguous_uint8() -> None:
    from error_coupling_simulator.carrier.records import RecordBatch

    det_source = np.array([[0, 1], [1, 0]], dtype=np.int16)
    obs_source = np.array([0, 1], dtype=np.int16)
    record = RecordBatch(det=det_source, obs=obs_source)

    assert record.det.dtype == np.uint8
    assert record.obs.dtype == np.uint8
    assert record.det.flags.c_contiguous
    assert record.obs.flags.c_contiguous
    assert not record.det.flags.writeable
    assert not record.obs.flags.writeable
    assert not np.shares_memory(record.det, det_source)
    assert not np.shares_memory(record.obs, obs_source)

    det_source[:] = 1
    obs_source[:] = 1
    np.testing.assert_array_equal(record.det, [[0, 1], [1, 0]])
    np.testing.assert_array_equal(record.obs, [0, 1])
    with pytest.raises(ValueError, match="read-only"):
        record.det[0, 0] = 1
    with pytest.raises(ValueError, match="read-only"):
        record.obs[0] = 1


@pytest.mark.parametrize(
    "payload",
    [
        np.array([[0.0, 0.0]], dtype=np.float64),
        np.array([[0.9, 0.0]], dtype=np.float64),
        np.array([[np.nan, 0.0]], dtype=np.float64),
        np.array([[np.inf, 0.0]], dtype=np.float64),
        np.array([[256, 0]], dtype=np.int64),
        np.array([[-256, 0]], dtype=np.int64),
        np.array([[0x02, 0]], dtype=np.uint8),
        np.array([[0x00, 2]], dtype=np.uint8),
    ],
)
def test_packed_shot_batch_rejects_noncanonical_payload(payload: np.ndarray) -> None:
    from error_coupling_simulator.carrier.records import PackedShotBatch

    with pytest.raises((TypeError, ValueError)):
        PackedShotBatch(
            header=_packed_header(),
            path=None,
            header_path=None,
            n_shots=1,
            syndrome_bits_per_shot=1,
            shots=payload,
        )


@pytest.mark.parametrize(
    ("field", "bad"),
    [
        ("format", "error_coupling_simulator.carrier.packed_shots.v2"),
        ("N", 2),
        ("syndrome_bits_per_shot", 2),
        ("out_stride_bytes", 3),
        ("syndrome_layout", "stabilizer-major"),
        ("detector_initial_prior", "unknown"),
        ("n_stab", 2),
        ("R", 2),
    ],
)
def test_packed_shot_batch_rejects_inconsistent_header(
    field: str, bad: object,
) -> None:
    from error_coupling_simulator.carrier.records import PackedShotBatch

    header = _packed_header()
    header[field] = bad
    with pytest.raises((TypeError, ValueError), match="header|format|layout"):
        PackedShotBatch(
            header=header,
            path=None,
            header_path=None,
            n_shots=1,
            syndrome_bits_per_shot=1,
            shots=np.array([[0x01, 0]], dtype=np.uint8),
        )


def test_packed_shot_batch_copies_and_revalidates_materialized_bytes() -> None:
    from error_coupling_simulator.carrier.records import PackedShotBatch

    source = np.array([[0x01, 0]], dtype=np.int16)
    batch = PackedShotBatch(
        header=_packed_header(),
        path=None,
        header_path=None,
        n_shots=1,
        syndrome_bits_per_shot=1,
        shots=source,
    )
    assert batch.shots is not None
    assert batch.shots.dtype == np.uint8
    assert batch.shots.flags.c_contiguous
    assert not batch.shots.flags.writeable
    assert not np.shares_memory(batch.shots, source)

    source[0, 0] = 0
    np.testing.assert_array_equal(batch.shots, [[0x01, 0]])
    with pytest.raises(ValueError, match="read-only"):
        batch.shots[0, 0] = 0

    # NumPy permits an owner to force its write flag back on. Conversion must
    # therefore validate the materialized bytes again instead of trusting init.
    batch.shots.setflags(write=True)
    batch.shots[0, 0] = 0x02
    with pytest.raises(ValueError, match="padding"):
        batch.to_raw_syndrome_obs()


@pytest.mark.parametrize(
    "payload",
    [
        np.array([[0.9, 0.0]], dtype=np.float64),
        np.array([[256, 0]], dtype=np.int64),
        np.array([[0x02, 0]], dtype=np.uint8),
    ],
)
def test_unpack_raw_syndrome_shots_revalidates_serialized_input(
    payload: np.ndarray,
) -> None:
    from error_coupling_simulator.carrier.records import unpack_raw_syndrome_shots

    with pytest.raises((TypeError, ValueError)):
        unpack_raw_syndrome_shots(payload, rounds=1, num_stabilizers=1)

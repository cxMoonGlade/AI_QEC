from __future__ import annotations

import numpy as np
import pytest


def test_record_fold_temporal_xor_round_trip_and_shape_contract() -> None:
    """The neutral carrier fold preserves the pinned temporal detector law."""

    from error_coupling_simulator.carrier.record_fold import det_to_s, s_to_det

    syndromes = np.asarray(
        [
            [0, 1, 1, 1, 1, 0],
            [1, 0, 1, 1, 0, 1],
        ],
        dtype=np.uint8,
    )
    expected_detectors = np.asarray(
        [
            [0, 1, 1, 0, 0, 1],
            [1, 0, 0, 1, 1, 0],
        ],
        dtype=np.uint8,
    )

    detectors = s_to_det(syndromes, R=3, n_stab=2)
    np.testing.assert_array_equal(detectors, expected_detectors)
    assert detectors.dtype == np.uint8
    assert detectors.shape == syndromes.shape
    np.testing.assert_array_equal(det_to_s(detectors, R=3, n_stab=2), syndromes)

    one_round = np.asarray([[1, 0, 1], [0, 1, 0]], dtype=np.uint8)
    np.testing.assert_array_equal(s_to_det(one_round, R=1, n_stab=3), one_round)
    np.testing.assert_array_equal(det_to_s(one_round, R=1, n_stab=3), one_round)

    with pytest.raises(ValueError, match=r"s_bits last axis 5 != R\*n_stab = 6"):
        s_to_det(np.zeros(5, dtype=np.uint8), R=3, n_stab=2)
    with pytest.raises(ValueError, match=r"det_bits last axis 5 != R\*n_stab = 6"):
        det_to_s(np.zeros(5, dtype=np.uint8), R=3, n_stab=2)
    with pytest.raises(ValueError, match="R and n_stab must be positive"):
        s_to_det(np.zeros(0, dtype=np.uint8), R=0, n_stab=2)
    with pytest.raises(ValueError, match="R and n_stab must be positive"):
        det_to_s(np.zeros(0, dtype=np.uint8), R=1, n_stab=0)

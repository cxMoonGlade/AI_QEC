from __future__ import annotations

import numpy as np
import pytest

from scope_static.physical.phyc1_contract import (
    FULL_CIRCUIT_DEPTH_SEMANTICS,
    FULL_CIRCUIT_TEACHER_MODEL,
    LOCAL_OBSERVABLE_TEACHER_MODEL,
    circuit_depth,
    counts_to_bit_matrix,
    full_circuit_depth_metadata,
    normalize_phyc1_teacher_model,
    probe_names,
)
from scope_static.physical.teacher import _counts_to_bit_matrix, _probe_names


def test_phyc1_contract_normalizes_teacher_model_aliases() -> None:
    assert normalize_phyc1_teacher_model({}) == FULL_CIRCUIT_TEACHER_MODEL
    assert normalize_phyc1_teacher_model({"physical_teacher_model": "cudaq-full-circuit"}) == FULL_CIRCUIT_TEACHER_MODEL
    assert normalize_phyc1_teacher_model({"teacher_model": "born_local"}) == LOCAL_OBSERVABLE_TEACHER_MODEL
    assert (
        normalize_phyc1_teacher_model({}, original_config={"backend": "local_observable_gpu"})
        == LOCAL_OBSERVABLE_TEACHER_MODEL
    )

    with pytest.raises(ValueError, match="physical_teacher_model"):
        normalize_phyc1_teacher_model({"physical_teacher_model": "not_a_teacher"})


def test_phyc1_contract_preserves_probe_and_counts_legacy_surface() -> None:
    assert probe_names("rzz_echo_no_echo") == _probe_names("rzz_echo_no_echo")
    assert len(probe_names("rzz_local_tomography")) == len(_probe_names("rzz_local_tomography"))

    rows = counts_to_bit_matrix({"00": 2, "11": 1, "0x2": 2}, shots=5, num_bits=2)
    legacy_rows = _counts_to_bit_matrix({"00": 2, "11": 1, "0x2": 2}, shots=5, num_bits=2)
    assert rows.dtype == np.uint8
    np.testing.assert_array_equal(rows, legacy_rows)


def test_phyc1_contract_literal_full_circuit_depth_metadata() -> None:
    assert circuit_depth({"depth": 0}) == 1
    assert circuit_depth({"num_layers": 7}) == 7
    assert full_circuit_depth_metadata(3) == {
        "circuit_depth": 3,
        "configured_circuit_depth": 3,
        "effective_circuit_depth": 3,
        "circuit_depth_semantics": FULL_CIRCUIT_DEPTH_SEMANTICS,
    }

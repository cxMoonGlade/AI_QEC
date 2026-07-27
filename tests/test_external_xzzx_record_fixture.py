"""Frozen contracts for the parameterized XZZX Record/PEPS fixture."""

from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
import stim


REPO = Path(__file__).resolve().parents[1]
EMITTER = (
    REPO
    / "scripts"
    / "external_baselines"
    / "emit_xzzx_record_peps_fixture.py"
)
PARENT_EMITTER = (
    REPO
    / "scripts"
    / "external_baselines"
    / "emit_xzzx_d7_capability_fixture.py"
)
PARENT_SHA256 = (
    "132fdc2d1eb56bf3791ad320bbb65b558e37350575e6174d4bd874cedb2c058d"
)
EXPECTED = {
    2: {
        "shape": (7, 10, 5, 1),
        "operations": 57,
        "resets": 6,
        "data": 4,
        "h_frame": 2,
        "detector_arities": {1: 1, 2: 3, 5: 1},
        "observable_arities": [2],
        "stim_sha256": (
            "18492ad9bc8b286d1cf9f97f45546fac40552a10d83be9ef61fa892a941cb671"
        ),
        "fixture_sha256": (
            "dbf2a0979c9a4cd0a95f2afe393083d97a27ea1e90720596352a191010beb0f5"
        ),
    },
    3: {
        "shape": (17, 25, 16, 1),
        "operations": 154,
        "resets": 16,
        "data": 9,
        "h_frame": 5,
        "detector_arities": {1: 4, 2: 8, 3: 2, 5: 2},
        "observable_arities": [3],
        "stim_sha256": (
            "7067b1241251bd7558e7dc85b2f84bc13a45c1217a49f8fcfa2e51205879ecb0"
        ),
        "fixture_sha256": (
            "3b2bf7d81f7241e0a3b6abb14c76474c362e696cf374c55e20e3d121946bbf3c"
        ),
    },
    5: {
        "shape": (49, 73, 48, 1),
        "operations": 490,
        "resets": 48,
        "data": 25,
        "h_frame": 13,
        "detector_arities": {1: 12, 2: 24, 3: 4, 5: 8},
        "observable_arities": [5],
        "stim_sha256": (
            "be26b8708efe36a027bcf79074bc936de552b1a5d22b35b627d7d9cdbb27f008"
        ),
        "fixture_sha256": (
            "659fda875a91f2a6e3c64f8f03487b5a431edecb9849dd897bf2e6f390583495"
        ),
    },
}


def _load_emitter():
    spec = importlib.util.spec_from_file_location(
        "emit_xzzx_record_peps_fixture_under_test",
        EMITTER,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("distance", [2, 3, 5])
def test_fixture_shape_stim_and_canonical_json_hashes_are_frozen(
    distance: int,
) -> None:
    emitter = _load_emitter()
    circuit, fixture = emitter.emit_fixture(stim, distance=distance, rounds=2)
    expected = EXPECTED[distance]

    assert fixture["schema"] == emitter.FIXTURE_SCHEMA
    assert fixture["distance"] == distance
    assert fixture["rounds"] == 2
    assert (
        fixture["num_qubits"],
        fixture["num_measurements"],
        fixture["num_detectors"],
        fixture["num_observables"],
    ) == expected["shape"]
    assert len(fixture["operations"]) == expected["operations"]
    assert fixture["stim_circuit_sha256"] == expected["stim_sha256"]
    assert (
        hashlib.sha256(str(circuit).encode("utf-8")).hexdigest()
        == expected["stim_sha256"]
    )
    assert emitter.canonical_json_sha256(fixture) == expected["fixture_sha256"]
    assert emitter.validate_fixture(fixture) == expected["fixture_sha256"]

    frame = fixture["frame"]
    assert len(frame["data_qubits"]) == expected["data"]
    assert len(frame["hadamard_frame_data_qubits"]) == expected["h_frame"]
    assert sorted(frame["dense_qubit_map"].values()) == list(
        range(expected["shape"][0])
    )
    assert Counter(map(len, fixture["detector_rows"])) == expected[
        "detector_arities"
    ]
    assert list(map(len, fixture["observable_rows"])) == expected[
        "observable_arities"
    ]

    measurements = fixture["measurement_order"]
    assert [row["column"] for row in measurements] == list(
        range(expected["shape"][1])
    )
    assert sum(row["reset"] for row in measurements) == expected["resets"]
    assert all(row["reset"] for row in measurements[: expected["resets"]])
    assert not any(row["reset"] for row in measurements[expected["resets"] :])


def test_d2_absolute_record_rows_and_data_order_are_frozen() -> None:
    emitter = _load_emitter()
    _circuit, fixture = emitter.emit_fixture(stim, distance=2, rounds=2)

    assert fixture["frame"]["data_qubits"] == [0, 2, 3, 5]
    assert fixture["detector_rows"] == [
        [1],
        [3, 0],
        [4, 1],
        [5, 2],
        [9, 8, 7, 6, 4],
    ]
    assert fixture["observable_rows"] == [[7, 6]]


def test_enumeration_and_run_specs_have_frozen_canonical_hashes() -> None:
    emitter = _load_emitter()
    _circuit, d2 = emitter.emit_fixture(stim, distance=2, rounds=2)
    enumeration = emitter.enumeration_spec(d2)
    assert emitter.canonical_json_sha256(enumeration) == (
        "02aef76a65383fbfec9a2f3e0b62a7dd0691a574ee739a4b6b33326ba13681ca"
    )
    assert enumeration["reference"] == {
        "method": "dense_complete_enumeration",
        "raw_outcome_count": 10,
        "support_size": 1024,
    }

    expected_runs = {
        3: (
            2026072603,
            "7dfa0a8ef9620712e6ea190aeda651c681295f9841963ce77686640255cc22a9",
        ),
        5: (
            2026072605,
            "06151ea1244495475259d40bf6ca7ad16cbdaf5f8184ee61b344fb2e81b413a4",
        ),
    }
    for distance, (seed, digest) in expected_runs.items():
        _circuit, fixture = emitter.emit_fixture(
            stim,
            distance=distance,
            rounds=2,
        )
        spec = emitter.run_spec(fixture)
        assert spec["schema"] == (
            "error_coupling_simulator.external_xzzx_record_peps.run_spec.v2"
        )
        assert spec["reference_branch"] == {
            "sampler": "numpy_exact_data_projector",
            "selector": {
                "algorithm": "sha256_prefix_born_v1",
                "comparison": (
                    "bit_0_iff_h_times_den_lt_num_times_2_pow_256_"
                    "for_p0_as_integer_ratio"
                ),
                "domain_separator_ascii": "ECS-XZZX-DATA-ONLY-BRANCH-V2",
                "domain_separator_terminated_by_zero_byte": True,
                "hash_integer_encoding": (
                    "sha256_full_digest_unsigned_big_endian"
                ),
                "measurement_column_encoding": (
                    "uint32_big_endian_equal_to_prefix_length"
                ),
                "prefix_encoding": "one_byte_per_bit_0x00_or_0x01",
                "seed": seed,
                "seed_encoding": "uint64_big_endian",
            },
            "shots": 1,
        }
        assert spec["reference_state"] == {
            "checkpoint": "after_round_1_ry_before_terminal_data_measurements",
            "method": "numpy_exact_data_projector",
            "probability_floor": None,
            "truncation": None,
        }
        assert emitter.canonical_json_sha256(spec) == digest
        assert emitter.validate_run_spec(spec, fixture) == digest


def test_v1_run_specs_are_explicit_legacy_objects_and_never_formal() -> None:
    emitter = _load_emitter()
    expected_legacy = {
        3: "11e86c8d205899d51440a7fab32dc31f046e723a047c4c7bc8fe9fed3f7e15b9",
        5: "092353542f2e9e329f4d3ed735d0e6a10caa88bc048478ee15cc06aefc60ef23",
    }
    for distance, digest in expected_legacy.items():
        _circuit, fixture = emitter.emit_fixture(
            stim,
            distance=distance,
            rounds=2,
        )
        legacy = emitter.legacy_v1_run_spec(fixture)
        assert legacy["schema"] == (
            "error_coupling_simulator.external_xzzx_record_peps.run_spec.v1"
        )
        assert legacy["reference_branch"]["sampler"] == (
            "qiskit_aer_matrix_product_state"
        )
        assert emitter.canonical_json_sha256(legacy) == digest
        with pytest.raises(ValueError, match="does not match"):
            emitter.validate_run_spec(legacy, fixture)


def test_fixture_validator_rejects_content_and_absolute_row_mutations() -> None:
    emitter = _load_emitter()
    _circuit, fixture = emitter.emit_fixture(stim, distance=3, rounds=2)

    changed_gate = copy.deepcopy(fixture)
    changed_gate["operations"][0]["op"] = "H"
    with pytest.raises(ValueError, match="canonical fixture SHA"):
        emitter.validate_fixture(changed_gate)

    changed_row = copy.deepcopy(fixture)
    changed_row["detector_rows"][-1] = changed_row["detector_rows"][-1][:-1]
    with pytest.raises(ValueError, match="canonical fixture SHA"):
        emitter.validate_fixture(changed_row)


def test_parent_d7_emitter_is_byte_frozen_and_not_imported() -> None:
    emitter_source = EMITTER.read_text(encoding="utf-8")
    assert hashlib.sha256(PARENT_EMITTER.read_bytes()).hexdigest() == PARENT_SHA256
    assert "emit_xzzx_d7_capability_fixture" not in emitter_source


def test_canonical_json_rejects_nonfinite_and_emitter_rejects_wrong_schedule() -> None:
    emitter = _load_emitter()
    with pytest.raises(ValueError):
        emitter.canonical_json_bytes({"bad": float("nan")})
    with pytest.raises(ValueError, match="rounds=2"):
        emitter.emit_fixture(stim, distance=3, rounds=3)
    with pytest.raises(ValueError, match="distance"):
        emitter.emit_fixture(stim, distance=4, rounds=2)


def test_emitter_output_preflight_requires_distinct_absent_targets_and_existing_parents(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    emitter = _load_emitter()
    fixture_path = tmp_path / "fixture.json"
    stim_path = tmp_path / "circuit.stim"
    spec_path = tmp_path / "spec.json"

    resolved = emitter.preflight_output_paths(
        (fixture_path, stim_path, spec_path)
    )
    assert resolved == (
        fixture_path.resolve(),
        stim_path.resolve(),
        spec_path.resolve(),
    )

    with pytest.raises(ValueError, match="pairwise distinct"):
        emitter.preflight_output_paths(
            (fixture_path, tmp_path / "." / "fixture.json")
        )

    fixture_path.write_bytes(b"do-not-replace")
    with pytest.raises(FileExistsError, match="refusing to replace"):
        emitter.preflight_output_paths((fixture_path, stim_path))
    with pytest.raises(FileExistsError):
        emitter._atomic_write(fixture_path, b"replacement")
    assert fixture_path.read_bytes() == b"do-not-replace"

    with pytest.raises(FileNotFoundError, match="parent directory"):
        emitter.preflight_output_paths(
            (tmp_path / "missing" / "fixture.json",)
        )

    raced_path = tmp_path / "raced.json"
    original_link = emitter.os.link

    def publish_after_racer(source, destination):
        Path(destination).write_bytes(b"racer-won")
        return original_link(source, destination)

    monkeypatch.setattr(emitter.os, "link", publish_after_racer)
    with pytest.raises(FileExistsError, match="refusing to replace"):
        emitter._atomic_write(raced_path, b"late-writer")
    assert raced_path.read_bytes() == b"racer-won"

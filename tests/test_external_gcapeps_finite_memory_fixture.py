"""Focused controls for the frozen neutral finite-memory fixture."""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


REPO = Path(__file__).resolve().parents[1]
EMITTER = (
    REPO
    / "scripts"
    / "external_baselines"
    / "emit_gcapeps_finite_memory_fixture.py"
)
EXPECTED_REPRESENTATIVE_SHA256 = (
    "43b3bea0f3cd30103cb88c39dcb0f760d3ee0e09e2041d4446b1a5a61952ceff"
)
EXPECTED_HELDOUT_LIST_SHA256 = {
    4: "c971ccffbeebe746faae7329c0649b6e66405a95fc2ecfc18f8c992fa71c53a2",
    6: "5dc0497317c9b192454d1b758bb6cfe472238b028ed89cd094e3ab28690f54b1",
}
EXPECTED_R4_GAMMA1_MATERIALIZATION_SHA256 = (
    "73f1c19b8eb84753d6e2d34875acb99f9438c0067a65125fc471f158473c8daa"
)


def _load_emitter():
    spec = importlib.util.spec_from_file_location(
        "emit_gcapeps_finite_memory_fixture_under_test",
        EMITTER,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fixture(
    *,
    rounds: int = 2,
    axis_family: int = 3,
    numerator: int = 4,
    ensemble: bool = False,
):
    emitter = _load_emitter()
    fixture = emitter.build_fixture(
        run_partition="HELDOUT",
        width=3,
        rounds=rounds,
        axis_family=axis_family,
        p_event_numerator=numerator,
        seed=emitter.HELDOUT_SEED,
        gamma_index=2,
        run_blpensemble=ensemble,
    )
    return emitter, fixture


def test_fixture_schema_geometry_inputs_gamma_and_projection_are_exact() -> None:
    emitter, fixture = _fixture(rounds=2, axis_family=2, numerator=2)

    assert fixture["schema"] == (
        "error_coupling_simulator.external.gcapeps_finite_memory.fixture.v1"
    )
    assert fixture["script_revision"] == (
        "gcapeps-finite-memory-neutral-fixture-v1"
    )
    assert fixture["fixture_id"] == fixture["case_id"]
    assert fixture["geometry"] == {
        "rows": 2,
        "width": 3,
        "n_qubits": 6,
        "system_sites": [0, 1, 2],
        "memory_sites": [3, 4, 5],
        "site_order": [
            {"site_id": 0, "row": "system", "row_index": 0},
            {"site_id": 1, "row": "system", "row_index": 1},
            {"site_id": 2, "row": "system", "row_index": 2},
            {"site_id": 3, "row": "memory", "row_index": 0},
            {"site_id": 4, "row": "memory", "row_index": 1},
            {"site_id": 5, "row": "memory", "row_index": 2},
        ],
        "graph_edges": [[0, 1], [0, 3], [1, 2], [1, 4], [2, 5], [3, 4], [4, 5]],
    }
    coordinate = fixture["coordinate_convention"]
    assert coordinate["qubit_order"] == list(range(6))
    assert coordinate["system_axes"] == [0, 1, 2]
    assert coordinate["memory_axes"] == [3, 4, 5]
    assert coordinate["q0_bit_significance"] == "most_significant"
    assert coordinate["tensor_axis_order"] == "S_0..S_(w-1),M_0..M_(w-1)"

    first, second = fixture["inputs"]
    assert first["dense_plain_initial_bits"] == [0] * 6
    assert first["gc_residual_initial_bits"] == [0] * 6
    assert first["gc_frame_preparation_gates"] == []
    assert second["dense_plain_initial_bits"] == [0, 1, 0, 0, 0, 0]
    assert second["gc_residual_initial_bits"] == [0] * 6
    assert second["gc_frame_preparation_gates"] == [
        {
            "operation_index": 0,
            "gate_kind": "X",
            "targets": [1],
            "matrix_definition": "X",
            "is_physical_round_gate": False,
        }
    ]
    assert (
        first["input_preparation_transcript_sha256"]
        != second["input_preparation_transcript_sha256"]
    )

    parameters = fixture["parameters"]
    assert parameters["active_axes"] == ["X", "Y"]
    assert parameters["p_event_denominator"] == 4
    assert parameters["gamma_index"] == 2
    assert parameters["gamma_label"] == "pi/7"
    assert parameters["gamma_float64_hex"] == "0x1.cb91f3bbba140p-2"
    assert parameters["theta_float64_hex"] == "-0x1.cb91f3bbba140p-2"
    assert float.fromhex(parameters["theta_float64_hex"]) == -float.fromhex(
        parameters["gamma_float64_hex"]
    )
    assert parameters["max_bond"] == 32
    assert fixture["checkpoints"] == [0, 1, 2]
    assert emitter.validate_fixture(fixture) == fixture[
        "result_projection_sha256"
    ]
    assert emitter.projection_sha256(fixture) == fixture[
        "result_projection_sha256"
    ]


def test_event_masks_are_prefix_stable_probability_nested_and_structural() -> None:
    emitter = _load_emitter()
    common = {
        "namespace": "CARRIER",
        "seed": 17,
        "mask_index": 0,
        "width": 7,
    }
    for round_index in range(1, 13):
        for site_index in range(7):
            bits = [
                emitter.event_bit(
                    **common,
                    round_index=round_index,
                    site_index=site_index,
                    p_event_numerator=numerator,
                )
                for numerator in range(5)
            ]
            assert bits[0] is False
            assert bits[4] is True
            assert bits == sorted(bits)

    short = emitter.build_fixture(
        run_partition="CALIBRATION",
        width=7,
        rounds=4,
        axis_family=3,
        p_event_numerator=3,
        seed=2,
        gamma_index=0,
        run_blpensemble=False,
    )
    long = emitter.build_fixture(
        run_partition="CALIBRATION",
        width=7,
        rounds=12,
        axis_family=3,
        p_event_numerator=3,
        seed=2,
        gamma_index=0,
        run_blpensemble=False,
    )
    short_rows = short["carrier_path"]["event_rows"]
    assert short_rows == long["carrier_path"]["event_rows"][: len(short_rows)]
    assert short["carrier_path"]["full_mask"] == long["carrier_path"][
        "full_mask"
    ][:4]

    payload = emitter.event_payload(
        **common,
        round_index=5,
        site_index=3,
    )
    expected = b"".join(
        (
            b"gcapeps-finite-memory-mask-v1\x00",
            b"CARRIER\x00",
            (17).to_bytes(8, "big"),
            (0).to_bytes(8, "big"),
            (7).to_bytes(8, "big"),
            (5).to_bytes(8, "big"),
            (3).to_bytes(8, "big"),
        )
    )
    assert payload == expected
    assert hashlib.sha256(payload).digest()[:8] == int.from_bytes(
        hashlib.sha256(payload).digest()[:8], "big"
    ).to_bytes(8, "big")


def test_round_gate_order_layers_and_separate_operation_views_are_frozen() -> None:
    _emitter, fixture = _fixture(rounds=1, axis_family=3, numerator=4)
    round_row = fixture["carrier_path"]["round_ledger"][0]

    assert round_row["round_index"] == 1
    assert [layer["layer_name"] for layer in round_row["layers"]] == [
        "system_h",
        "system_s",
        "system_cx_parity_1",
        "system_cx_parity_0",
        "memory_reverse_cx_parity_1",
        "memory_reverse_cx_parity_0",
        "event_conditioned_collisions",
    ]
    assert [layer["parity"] for layer in round_row["layers"]] == [
        1,
        0,
        1,
        0,
        1,
        0,
        None,
    ]
    operations = round_row["operations"]
    assert [operation["operation_index"] for operation in operations] == list(
        range(len(operations))
    )
    assert [
        operation["operation_index"]
        for operation in round_row["clifford_operations"]
    ] == list(range(7))
    assert [
        operation["operation_index"]
        for operation in round_row["collision_rotations"]
    ] == list(range(7, 16))
    assert [
        (operation["gate_kind"], operation["targets"])
        for operation in round_row["clifford_operations"]
    ] == [
        ("H", [1]),
        ("S", [0]),
        ("S", [2]),
        ("CX", [1, 2]),
        ("CX", [0, 1]),
        ("CX", [5, 4]),
        ("CX", [4, 3]),
    ]
    assert [
        (
            rotation["site_index"],
            rotation["axis"],
            rotation["axis_index"],
            rotation["targets"],
            rotation["physical_pauli_body"],
        )
        for rotation in round_row["collision_rotations"]
    ] == [
        (0, "X", 0, [0, 3], "XIIXII"),
        (0, "Y", 1, [0, 3], "YIIYII"),
        (0, "Z", 2, [0, 3], "ZIIZII"),
        (1, "X", 0, [1, 4], "IXIIXI"),
        (1, "Y", 1, [1, 4], "IYIIYI"),
        (1, "Z", 2, [1, 4], "IZIIZI"),
        (2, "X", 0, [2, 5], "IIXIIX"),
        (2, "Y", 1, [2, 5], "IIYIIY"),
        (2, "Z", 2, [2, 5], "IIZIIZ"),
    ]
    assert [rotation["collision_ordinal"] for rotation in round_row[
        "collision_rotations"
    ]] == list(range(9))
    assert [
        index
        for layer in round_row["layers"]
        for index in layer["operation_indices"]
    ] == list(range(16))


def test_p_zero_has_no_collision_and_ensemble_keeps_all_duplicate_paths() -> None:
    emitter, fixture = _fixture(
        rounds=2,
        axis_family=3,
        numerator=0,
        ensemble=True,
    )
    carrier = fixture["carrier_path"]
    assert carrier["realized_event_count"] == 0
    assert carrier["active_axis_rotation_count"] == 0
    assert carrier["full_mask"] == [[False] * 3, [False] * 3]
    assert all(
        round_row["collision_rotations"] == []
        for round_row in carrier["round_ledger"]
    )
    assert fixture["sdim_pullback_requests"] == []

    ensemble = fixture["blpensemble"]
    assert ensemble["enabled"] is True
    assert ensemble["registered_path_count"] == 32
    assert ensemble["path_count"] == 32
    assert ensemble["distinct_mask_count"] == 1
    assert [path["mask_index"] for path in ensemble["paths"]] == list(range(32))
    assert all(path["weight_numerator"] == 1 for path in ensemble["paths"])
    assert all(path["weight_denominator"] == 32 for path in ensemble["paths"])
    assert all(path["mask_multiplicity"] == 32 for path in ensemble["paths"])
    assert all(path["distinct_mask_count"] == 1 for path in ensemble["paths"])
    assert len({path["full_mask_sha256"] for path in ensemble["paths"]}) == 1
    assert emitter.validate_fixture(fixture) == fixture[
        "result_projection_sha256"
    ]


def test_pullback_requests_have_exact_sorted_unique_keys_for_both_inputs() -> None:
    emitter, fixture = _fixture(rounds=1, axis_family=3, numerator=4)
    requests = fixture["sdim_pullback_requests"]
    assert len(requests) == 2 * 3 * 3
    assert all(set(row) == set(emitter.PULLBACK_REQUEST_KEYS) for row in requests)
    keys = [
        tuple(row[field] for field in emitter.PULLBACK_REQUEST_KEYS)
        for row in requests
    ]
    assert keys == sorted(keys)
    assert len(keys) == len(set(keys))
    assert {row["input_id"] for row in requests} == {1, 2}
    assert all(row["round_prefix"] == row["round_index"] == 1 for row in requests)
    assert all(row["shared_evolution_transcript_sha256"] == fixture[
        "carrier_path"
    ]["shared_evolution_transcript_sha256"] for row in requests)
    preparation_hashes = {
        row["input_id"]: row["input_preparation_transcript_sha256"]
        for row in fixture["inputs"]
    }
    assert all(
        row["input_preparation_transcript_sha256"]
        == preparation_hashes[row["input_id"]]
        for row in requests
    )


@pytest.mark.parametrize(("rounds_star", "expected_count"), [(4, 11), (6, 12)])
def test_heldout_union_uses_five_integer_tuples_and_frozen_memberships(
    rounds_star: int,
    expected_count: int,
) -> None:
    emitter = _load_emitter()
    rows = emitter.build_heldout_cells(rounds_star)
    cells = [tuple(row["cell"]) for row in rows]

    assert len(rows) == expected_count
    assert cells == sorted(cells)
    assert len(cells) == len(set(cells))
    assert all(len(cell) == 5 for cell in cells)
    assert all(all(type(value) is int for value in cell) for cell in cells)
    assert all(cell[-1] == 4 for cell in cells)
    assert all(
        row["slice_membership"]
        == [
            member
            for member in emitter.SLICE_ORDER
            if member in row["slice_membership"]
        ]
        for row in rows
    )
    assert all(
        row["run_blpensemble"]
        == ("probability" in row["slice_membership"])
        for row in rows
    )
    stress = next(row for row in rows if row["cell"] == [7, rounds_star, 3, 3, 4])
    assert stress["slice_membership"] == [
        "width",
        "rounds",
        "axis_family",
        "probability",
    ]
    assert stress["run_blpensemble"] is True
    assert emitter.heldout_cell_list_sha256(rounds_star) == emitter.canonical_sha256(
        rows
    )
    assert emitter.heldout_cell_list_sha256(rounds_star) == (
        EXPECTED_HELDOUT_LIST_SHA256[rounds_star]
    )


def test_heldout_union_rejects_a_round_count_outside_calibration_grid() -> None:
    with pytest.raises(ValueError, match="calibration grid"):
        _load_emitter().build_heldout_cells(3)


def test_heldout_seed_and_complete_materialization_are_deterministic() -> None:
    emitter = _load_emitter()
    expected_seed = int.from_bytes(
        hashlib.sha256(b"gcapeps-finite-memory-heldout-v1").digest()[:8],
        "big",
    )
    assert emitter.HELDOUT_SEED == expected_seed

    first = emitter.materialize_heldout_fixtures(rounds_star=4, gamma_index=1)
    second = emitter.materialize_heldout_fixtures(rounds_star=4, gamma_index=1)
    assert emitter.canonical_json_bytes(first) == emitter.canonical_json_bytes(
        second
    )
    assert first["cell_list_sha256"] == emitter.heldout_cell_list_sha256(4)
    assert first["heldout_fixture_sha256"] == (
        EXPECTED_R4_GAMMA1_MATERIALIZATION_SHA256
    )
    assert len(first["fixtures"]) == 11
    assert len(first["fixture_projection_sha256s"]) == 11
    assert all(
        emitter.validate_fixture(fixture)
        == fixture["result_projection_sha256"]
        for fixture in first["fixtures"]
    )
    representative = emitter.build_fixture(
        run_partition="HELDOUT",
        width=3,
        rounds=1,
        axis_family=3,
        p_event_numerator=4,
        seed=emitter.HELDOUT_SEED,
        gamma_index=0,
        run_blpensemble=False,
    )
    assert representative["result_projection_sha256"] == (
        EXPECTED_REPRESENTATIVE_SHA256
    )


def test_validation_rejects_event_order_gamma_and_projection_corruption() -> None:
    emitter, fixture = _fixture(rounds=1, axis_family=1, numerator=3)

    wrong_event = copy.deepcopy(fixture)
    wrong_event["carrier_path"]["event_rows"][0]["event"] = not wrong_event[
        "carrier_path"
    ]["event_rows"][0]["event"]
    with pytest.raises(ValueError, match="deterministic reconstruction"):
        emitter.validate_fixture(wrong_event)

    wrong_order = copy.deepcopy(fixture)
    operations = wrong_order["carrier_path"]["round_ledger"][0]["operations"]
    operations[0], operations[1] = operations[1], operations[0]
    with pytest.raises(ValueError, match="deterministic reconstruction"):
        emitter.validate_fixture(wrong_order)

    wrong_gamma = copy.deepcopy(fixture)
    wrong_gamma["parameters"]["theta_float64_hex"] = (
        wrong_gamma["parameters"]["gamma_float64_hex"]
    )
    with pytest.raises(ValueError, match="deterministic reconstruction"):
        emitter.validate_fixture(wrong_gamma)

    wrong_hash = copy.deepcopy(fixture)
    wrong_hash["result_projection_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="deterministic reconstruction"):
        emitter.validate_fixture(wrong_hash)


def test_generator_has_no_candidate_reference_or_simulator_imports() -> None:
    source = EMITTER.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(EMITTER))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(
                alias.name.split(".", 1)[0] for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
    assert imported_roots.isdisjoint(
        {
            "numpy",
            "quimb",
            "stim",
            "sdim",
            "gcapeps",
            "error_coupling_simulator",
        }
    )


def test_cli_emits_one_exact_compact_json_core_without_newline() -> None:
    process = subprocess.run(
        [
            sys.executable,
            "-I",
            str(EMITTER),
            "--run-partition",
            "HELDOUT",
            "--width",
            "3",
            "--rounds",
            "1",
            "--axis-family",
            "1",
            "--p-event-numerator",
            "0",
            "--seed",
            str(_load_emitter().HELDOUT_SEED),
            "--gamma-index",
            "0",
        ],
        check=True,
        capture_output=True,
    )
    assert process.stderr == b""
    assert process.stdout.endswith(b"}")
    assert not process.stdout.endswith(b"\n")
    payload = json.loads(process.stdout)
    emitter = _load_emitter()
    assert process.stdout == emitter.canonical_json_bytes(payload)
    assert emitter.validate_fixture(payload) == payload[
        "result_projection_sha256"
    ]

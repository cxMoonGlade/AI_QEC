"""Frozen contracts for the neutral GCAPEPS d=3/5/7 prefix fixture."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

import pytest
import stim


REPO = Path(__file__).resolve().parents[1]
EMITTER = (
    REPO
    / "scripts"
    / "external_baselines"
    / "emit_gcapeps_d357_unitary_prefix_fixture.py"
)
EXPECTED = {
    3: {
        "n_qubits": 17,
        "h_count": 37,
        "cx_count": 24,
        "gate_count": 61,
        "edge_count": 24,
        "gate_stream_sha256": (
            "e8d5686a6ebb8c9ac9522a8dd623ff30f14cea89bb881e411a9ddaf0b9183c4b"
        ),
        "edge_stream_sha256": (
            "d57e8b13c831565d4ecc327aa6481745a7d393055983acc76eb46a7e34cc5a51"
        ),
        "transformed_sha256": (
            "7067b1241251bd7558e7dc85b2f84bc13a45c1217a49f8fcfa2e51205879ecb0"
        ),
        "target": 6,
        "xy": [3, 3],
        "signed_pullback": "-_____XYX____X_X__",
        "support": [5, 6, 7, 12, 14],
        "operator_elements": 144,
        "candidate_elements": 72,
    },
    5: {
        "n_qubits": 49,
        "h_count": 117,
        "cx_count": 80,
        "gate_count": 197,
        "edge_count": 80,
        "gate_stream_sha256": (
            "44f13a5e55332af5009d78194ad99598d794172ca0bc7b0e1437ae67b12ac164"
        ),
        "edge_stream_sha256": (
            "754033fa23821b43e7bbb14f179f8e3e863d8ff75e63ae8e76fae9cf23c25021"
        ),
        "transformed_sha256": (
            "be26b8708efe36a027bcf79074bc936de552b1a5d22b35b627d7d9cdbb27f008"
        ),
        "target": 22,
        "xy": [5, 5],
        "signed_pullback": (
            "-_____________________XYX______X_X________________"
        ),
        "support": [21, 22, 23, 30, 32],
        "operator_elements": 272,
        "candidate_elements": 136,
    },
    7: {
        "n_qubits": 97,
        "h_count": 241,
        "cx_count": 168,
        "gate_count": 409,
        "edge_count": 168,
        "gate_stream_sha256": (
            "bd99a17547d398895992910ac9c836aceba05dfe82ccf261a9050cf42d71a5aa"
        ),
        "edge_stream_sha256": (
            "ea3449fb76aa214de37e7b73e4f32c19eb68ff37309b38875e7056dda1d04c50"
        ),
        "transformed_sha256": (
            "193d56d199b45016d91e8d5742f52fdc4e8e3b74d571891c78e28f7ec4eca6bd"
        ),
        "target": 44,
        "xy": [7, 7],
        "signed_pullback": (
            "-___________________________________________XYX____________X_X"
            "____________________________________"
        ),
        "support": [43, 44, 45, 58, 60],
        "operator_elements": 464,
        "candidate_elements": 232,
    },
}

V2_EXPECTED = {
    3: {
        "fixture_sha256": (
            "1b039174dc8b657efcb398cf0b9cfc29556e14e088a7a898b2824880407c420d"
        ),
        "grid_sha256": (
            "f0690114ed3652421d11161aa32ca486384cb17a9d191d9d68884651b23bc97a"
        ),
        "schedule_sha256": (
            "f3f126b3b1adb07fd090c39a9c93f55bcf6626a97836f2379b70de7a6bf10ac5"
        ),
        "locations": (
            (6, "data", [3, 3]),
            (5, "check", [2, 2]),
            (7, "check", [4, 2]),
            (12, "check", [2, 4]),
        ),
    },
    5: {
        "fixture_sha256": (
            "ebafd1ef5f7f86cf55bb792dcf191c3c96fa8c8b02f6836cde7fba960385eac3"
        ),
        "grid_sha256": (
            "766fe3130bbd4751801ae548699796781b82ad9609447661d44574e8f83fdb74"
        ),
        "schedule_sha256": (
            "09dce6c4e14b651d41424c3f8c9ee8636569ff6ae9baf6bf39e8a718fecfa83f"
        ),
        "locations": (
            (22, "data", [5, 5]),
            (21, "check", [4, 4]),
            (23, "check", [6, 4]),
            (30, "check", [4, 6]),
        ),
    },
    7: {
        "fixture_sha256": (
            "727ec6d223a32a5d855df952a88abaa122ce0f20ce4c014af6a921396ea73f9a"
        ),
        "grid_sha256": (
            "1091503728805c068cbb424b8fcc658a96793d732e9b6d0c537190b5333b9ada"
        ),
        "schedule_sha256": (
            "2d9ed4424fcaf62ae8f14fa17ed7f62d93aa4364207a654ba090fa2bc822ccc9"
        ),
        "locations": (
            (44, "data", [7, 7]),
            (43, "check", [6, 6]),
            (45, "check", [8, 6]),
            (58, "check", [6, 8]),
        ),
    },
}
GRID_SPEC = (
    ("baseline", 1, 1, 1e-3),
    ("depth-2", 2, 1, 1e-3),
    ("depth-d", "distance", 1, 1e-3),
    ("complexity-2", 1, 2, 1e-3),
    ("complexity-4", 1, 4, 1e-3),
    ("low-probability", 1, 1, 1e-4),
    ("high-probability", 1, 1, 1e-2),
    ("stress-corner", "distance", 4, 1e-2),
)


def _load_emitter():
    spec = importlib.util.spec_from_file_location(
        "emit_gcapeps_d357_unitary_prefix_fixture_under_test",
        EMITTER,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fixture(distance: int):
    emitter = _load_emitter()
    circuit, fixture = emitter.emit_fixture(stim, distance=distance)
    return emitter, circuit, fixture


@pytest.mark.parametrize("distance", [3, 5, 7])
def test_preregistered_counts_and_hashes_are_pinned(distance: int) -> None:
    emitter, circuit, fixture = _fixture(distance)
    expected = EXPECTED[distance]

    assert fixture["schema"] == emitter.FIXTURE_SCHEMA
    assert fixture["fixture_id"] == f"gcapeps-d{distance}-unitary-prefix-v2"
    assert fixture["distance"] == distance
    assert fixture["n_qubits"] == expected["n_qubits"]
    assert fixture["dtype"] == "complex128"
    assert fixture["stim_source"]["generator"] == (
        "surface_code:rotated_memory_z"
    )
    assert fixture["stim_source"]["rounds"] == 2
    assert fixture["stim_source"]["first_measurement"] == "MR"
    assert fixture["stim_source"]["transformed_sha256"] == expected[
        "transformed_sha256"
    ]
    assert hashlib.sha256(str(circuit).encode("utf-8")).hexdigest() == expected[
        "transformed_sha256"
    ]

    prefix = fixture["prefix"]
    assert prefix["h_count"] == expected["h_count"]
    assert prefix["cx_count"] == expected["cx_count"]
    assert prefix["gate_count"] == expected["gate_count"]
    assert prefix["gate_stream_sha256"] == expected["gate_stream_sha256"]
    assert [row["index"] for row in prefix["gates"]] == list(
        range(expected["gate_count"])
    )
    assert {row["token"] for row in prefix["gates"]} == {"H", "CX"}
    assert all(len(row["matrix_sha256"]) == 64 for row in prefix["gates"])

    graph = fixture["graph"]
    assert graph["edge_count"] == expected["edge_count"]
    assert graph["edge_stream_sha256"] == expected["edge_stream_sha256"]
    assert len(graph["edges"]) == len({tuple(edge) for edge in graph["edges"]})

    digest = emitter.validate_fixture(fixture)
    assert digest == emitter.EXPECTED[distance]["fixture_sha256"]
    assert digest == V2_EXPECTED[distance]["fixture_sha256"]
    assert emitter.canonical_json_sha256(fixture) == digest


@pytest.mark.parametrize("distance", [3, 5, 7])
def test_rotated_coordinates_compact_graph_and_center_star(distance: int) -> None:
    _emitter, _circuit, fixture = _fixture(distance)
    expected = EXPECTED[distance]

    coordinates = fixture["coordinate_map"]
    assert [row["compact_qubit"] for row in coordinates] == list(
        range(expected["n_qubits"])
    )
    assert [row["original_stim_qubit"] for row in coordinates] == sorted(
        row["original_stim_qubit"] for row in coordinates
    )
    rotated = [tuple(row["rotated_row_col"]) for row in coordinates]
    assert len(set(rotated)) == expected["n_qubits"]
    assert all(
        0 <= coordinate <= 2 * distance - 2
        for row_col in rotated
        for coordinate in row_col
    )

    by_compact = {row["compact_qubit"]: row for row in coordinates}
    for left, right in fixture["graph"]["edges"]:
        lr = by_compact[left]["rotated_row_col"]
        rr = by_compact[right]["rotated_row_col"]
        assert abs(lr[0] - rr[0]) + abs(lr[1] - rr[1]) == 1

    nonclifford = fixture["nonclifford"]
    target = nonclifford["target"]
    assert target == expected["target"]
    assert by_compact[target]["xy"] == expected["xy"]
    assert target in fixture["stim_source"]["rx_initialized_compact_qubits"]
    incident = [
        edge for edge in fixture["graph"]["edges"] if target in edge
    ]
    assert len(incident) == 4
    assert nonclifford["routing_edges"] == incident
    assert sorted(
        {qubit for edge in incident for qubit in edge}
    ) == expected["support"]


@pytest.mark.parametrize("distance", [3, 5, 7])
def test_stim_exact_signed_pullback_support_and_star(distance: int) -> None:
    _emitter, _circuit, fixture = _fixture(distance)
    expected = EXPECTED[distance]
    prefix_circuit = stim.Circuit()
    for row in fixture["prefix"]["gates"]:
        prefix_circuit.append(row["token"], row["targets"])

    target = fixture["nonclifford"]["target"]
    pullback = str(
        stim.Tableau.from_circuit(prefix_circuit).inverse().y_output(target)
    )
    support = [
        index for index, pauli in enumerate(pullback[1:]) if pauli != "_"
    ]

    assert pullback == expected["signed_pullback"]
    assert pullback == fixture["nonclifford"]["signed_pullback"]
    assert support == expected["support"]
    assert support == fixture["nonclifford"]["support"]
    assert len(fixture["nonclifford"]["routing_edges"]) == 4


@pytest.mark.parametrize("distance", [3, 5, 7])
def test_nonclifford_and_resource_contract_are_exact(distance: int) -> None:
    _emitter, _circuit, fixture = _fixture(distance)
    expected = EXPECTED[distance]

    assert fixture["nonclifford"] == {
        "physical_pauli": "Y",
        "target": expected["target"],
        "angle_radians": 0.137,
        "active_rank": 2,
        "signed_pullback": expected["signed_pullback"],
        "support": expected["support"],
        "routing_edges": fixture["nonclifford"]["routing_edges"],
    }
    assert fixture["gcapeps_resource_expectations"] == {
        "max_local_operator_elements": 64,
        "max_total_operator_elements": expected["operator_elements"],
        "max_local_candidate_tensor_elements": 32,
        "max_total_candidate_tensor_elements": expected["candidate_elements"],
        "max_predicted_bond_dimension": 2,
        "max_routed_rank_product": 2,
        "max_total_bond_growth_product": 2,
        "expected_refactor_factor_product": 1,
    }
    assert fixture["peps_settings"] == {
        "cutoff": 1e-12,
        "renorm": False,
        "gauge_smudge": 0.0,
        "equilibrate_every": None,
        "max_bond": None,
        "to_backend": None,
        "convert_eager": True,
    }


def test_validation_rejects_signed_pullback_coordinate_and_stream_corruption() -> None:
    emitter, _circuit, fixture = _fixture(3)

    wrong_sign = copy.deepcopy(fixture)
    wrong_sign["nonclifford"]["signed_pullback"] = (
        "+" + wrong_sign["nonclifford"]["signed_pullback"][1:]
    )
    with pytest.raises(ValueError, match="signed pullback"):
        emitter.validate_fixture(wrong_sign)

    wrong_coordinate = copy.deepcopy(fixture)
    wrong_coordinate["coordinate_map"][0]["rotated_row_col"][0] += 1
    with pytest.raises(ValueError, match="rotated coordinate"):
        emitter.validate_fixture(wrong_coordinate)

    wrong_gate = copy.deepcopy(fixture)
    wrong_gate["prefix"]["gates"][0]["targets"][0] += 1
    with pytest.raises(ValueError, match="gate stream"):
        emitter.validate_fixture(wrong_gate)


def test_cli_writes_canonical_outputs_exclusively(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    emitter = _load_emitter()
    json_path = tmp_path / "fixture.json"
    stim_path = tmp_path / "fixture.stim"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(EMITTER),
            "--distance",
            "3",
            "--output-json",
            str(json_path),
            "--output-stim",
            str(stim_path),
        ],
    )

    assert emitter.main() == 0
    fixture = json.loads(json_path.read_text(encoding="utf-8"))
    assert json_path.read_bytes() == emitter.canonical_json_bytes(fixture)
    assert hashlib.sha256(stim_path.read_bytes()).hexdigest() == EXPECTED[3][
        "transformed_sha256"
    ]

    with pytest.raises(FileExistsError, match="refusing to replace"):
        emitter.main()


def test_cli_preflight_rejects_aliasing_and_missing_parent(tmp_path: Path) -> None:
    emitter = _load_emitter()
    destination = tmp_path / "same"
    with pytest.raises(ValueError, match="pairwise distinct"):
        emitter.preflight_output_paths((destination, destination))
    with pytest.raises(FileNotFoundError, match="parent directory"):
        emitter.preflight_output_paths(
            (tmp_path / "missing" / "fixture.json",)
        )


@pytest.mark.parametrize("distance", [3, 5, 7])
def test_v2_error_location_order_grid_and_angle_hex_are_frozen(
    distance: int,
) -> None:
    emitter, _circuit, fixture = _fixture(distance)
    expected = V2_EXPECTED[distance]
    locations = fixture["error_locations"]

    assert [
        (row["target"], row["kind"], row["xy"]) for row in locations
    ] == list(expected["locations"])
    assert [row["location_rank"] for row in locations] == [1, 2, 3, 4]
    assert fixture["error_locations_sha256"] == (
        emitter.canonical_json_sha256(locations)
    )

    cells = fixture["grid_cells"]
    assert len(cells) == 8
    assert len({cell["cell_id"] for cell in cells}) == 8
    for cell, (role, layer_spec, complexity, probability) in zip(
        cells, GRID_SPEC, strict=True
    ):
        layers = distance if layer_spec == "distance" else layer_spec
        theta = 2.0 * math.asin(math.sqrt(float(probability)))
        assert cell["cell_id"] == f"d{distance}-{role}"
        assert cell["role"] == role
        assert cell["round_layers"] == layers
        assert cell["noise_complexity"] == complexity
        assert cell["p_twirl"] == float(probability)
        assert cell["p_twirl_float64_hex"] == float(probability).hex()
        assert cell["theta_radians"] == theta
        assert cell["theta_float64_hex"] == theta.hex()
        assert cell["selected_targets"] == [
            row["target"] for row in locations[:complexity]
        ]
        assert cell["prefix_application_count"] == layers
        assert cell["rotation_count"] == layers * complexity

        ledger = cell["operation_ledger"]
        assert [row["operation_index"] for row in ledger] == list(
            range(layers * (complexity + 1))
        )
        cursor = 0
        for layer in range(1, layers + 1):
            assert ledger[cursor] == {
                "operation_index": cursor,
                "layer": layer,
                "kind": "clifford_prefix",
                "prefix_gate_count": fixture["prefix"]["gate_count"],
                "prefix_gate_stream_sha256": fixture["prefix"][
                    "gate_stream_sha256"
                ],
            }
            cursor += 1
            for location in locations[:complexity]:
                assert ledger[cursor] == {
                    "operation_index": cursor,
                    "layer": layer,
                    "kind": "physical_ry",
                    "location_rank": location["location_rank"],
                    "target": location["target"],
                    "theta_radians": theta,
                    "theta_float64_hex": theta.hex(),
                }
                cursor += 1

    assert fixture["grid_cells_sha256"] == expected["grid_sha256"]
    assert fixture["grid_cells_sha256"] == emitter.canonical_json_sha256(cells)


@pytest.mark.parametrize("distance", [3, 5, 7])
def test_accumulated_frame_schedule_replays_every_layer_and_location(
    distance: int,
) -> None:
    emitter, _circuit, fixture = _fixture(distance)
    prefix = stim.Circuit()
    for gate in fixture["prefix"]["gates"]:
        prefix.append(gate["token"], gate["targets"])

    accumulated = stim.Circuit()
    schedule = fixture["accumulated_frame_schedule"]
    rows = schedule["rows"]
    assert len(rows) == 4 * distance
    cursor = 0
    for layer in range(1, distance + 1):
        accumulated += prefix
        inverse = stim.Tableau.from_circuit(accumulated).inverse()
        for location in fixture["error_locations"]:
            pullback = str(inverse.y_output(location["target"]))
            support = [
                index
                for index, pauli in enumerate(pullback[1:])
                if pauli != "_"
            ]
            assert rows[cursor] == {
                "layer": layer,
                "location_rank": location["location_rank"],
                "target": location["target"],
                "signed_pullback": pullback,
                "support": support,
            }
            cursor += 1

    assert rows[0]["signed_pullback"] == fixture["nonclifford"][
        "signed_pullback"
    ]
    assert rows[0]["support"] == fixture["nonclifford"]["support"]
    assert schedule["schedule_sha256"] == V2_EXPECTED[distance][
        "schedule_sha256"
    ]
    assert schedule["schedule_sha256"] == emitter.canonical_json_sha256(rows)


@pytest.mark.parametrize("distance", [3, 5, 7])
def test_v2_multi_update_hard_guard_is_exact(distance: int) -> None:
    _emitter, _circuit, fixture = _fixture(distance)
    assert fixture["gcapeps_multi_resource_limits"] == {
        "max_local_operator_elements": 64,
        "max_total_operator_elements": 64 * fixture["n_qubits"],
        "max_local_candidate_tensor_elements": 4_194_304,
        "max_total_candidate_tensor_elements": 16_777_216,
        "max_predicted_bond_dimension": 64,
        "max_routed_rank_product": 64,
        "max_total_bond_growth_product": 64,
        "expected_refactor_factor_product": 1,
    }


def test_v2_mutations_of_grid_frame_site_order_and_guard_fail_closed() -> None:
    emitter, _circuit, fixture = _fixture(3)

    wrong_order = copy.deepcopy(fixture)
    wrong_order["error_locations"][0], wrong_order["error_locations"][1] = (
        wrong_order["error_locations"][1],
        wrong_order["error_locations"][0],
    )
    with pytest.raises(ValueError, match="error locations"):
        emitter.validate_fixture(wrong_order)

    wrong_kind = copy.deepcopy(fixture)
    wrong_kind["error_locations"][1]["kind"] = "data"
    with pytest.raises(ValueError, match="error locations"):
        emitter.validate_fixture(wrong_kind)

    for field, value in (
        ("round_layers", 2),
        ("noise_complexity", 2),
        ("p_twirl", 0.002),
        ("theta_float64_hex", "0x1.0p+0"),
    ):
        corrupted = copy.deepcopy(fixture)
        corrupted["grid_cells"][0][field] = value
        with pytest.raises(ValueError, match="grid cell"):
            emitter.validate_fixture(corrupted)

    wrong_operation = copy.deepcopy(fixture)
    wrong_operation["grid_cells"][0]["operation_ledger"][1]["target"] = 5
    with pytest.raises(ValueError, match="operation ledger"):
        emitter.validate_fixture(wrong_operation)

    wrong_frame = copy.deepcopy(fixture)
    wrong_frame["accumulated_frame_schedule"]["rows"][4][
        "signed_pullback"
    ] = wrong_frame["accumulated_frame_schedule"]["rows"][0][
        "signed_pullback"
    ]
    with pytest.raises(ValueError, match="accumulated frame"):
        emitter.validate_fixture(wrong_frame)

    wrong_guard = copy.deepcopy(fixture)
    wrong_guard["gcapeps_multi_resource_limits"][
        "max_predicted_bond_dimension"
    ] = 63
    with pytest.raises(ValueError, match="hard guard"):
        emitter.validate_fixture(wrong_guard)

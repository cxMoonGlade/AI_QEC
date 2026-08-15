#!/usr/bin/env python3
"""Emit the neutral GCAPEPS d=3/5/7 first-measurement prefix fixture.

The source is Stim's noiseless rotated-memory-Z circuit with the audited
checkerboard local-H XZZX conjugation.  Sparse Stim ids are compacted, then
the fixture retains only the chronological unitary prefix before the first
``MR``: resets declare the product input, ``RX`` becomes ``H``, and existing
``H``/ordered ``CX`` gates are retained.

This is a performance fixture for two equal-status candidates.  It contains
no measurement/Record estimand and supplies no large-state truth claim.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import tempfile
from typing import Any


FIXTURE_SCHEMA = (
    "error_coupling_simulator.external_gcapeps_d357_unitary_prefix.fixture.v2"
)
SUPPORTED_DISTANCES = (3, 5, 7)
SOURCE_ROUNDS = 2
ANGLE_RADIANS = 0.137
GRID_ROLE_SPECS = (
    ("baseline", 1, 1, 1e-3),
    ("depth-2", 2, 1, 1e-3),
    ("depth-d", "distance", 1, 1e-3),
    ("complexity-2", 1, 2, 1e-3),
    ("complexity-4", 1, 4, 1e-3),
    ("low-probability", 1, 1, 1e-4),
    ("high-probability", 1, 1, 1e-2),
    ("stress-corner", "distance", 4, 1e-2),
)
EXPECTED: dict[int, dict[str, Any]] = {
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
        "max_total_operator_elements": 144,
        "max_total_candidate_tensor_elements": 72,
        "error_locations": [6, 5, 7, 12],
        "error_locations_sha256": (
            "4536b7e44dac1b6cb6751373a2f0802b03df8456a58fd128938b7216508dc412"
        ),
        "grid_cells_sha256": (
            "f0690114ed3652421d11161aa32ca486384cb17a9d191d9d68884651b23bc97a"
        ),
        "accumulated_frame_schedule_sha256": (
            "f3f126b3b1adb07fd090c39a9c93f55bcf6626a97836f2379b70de7a6bf10ac5"
        ),
        "fixture_sha256": (
            "1b039174dc8b657efcb398cf0b9cfc29556e14e088a7a898b2824880407c420d"
        ),
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
        "max_total_operator_elements": 272,
        "max_total_candidate_tensor_elements": 136,
        "error_locations": [22, 21, 23, 30],
        "error_locations_sha256": (
            "e85afeec3861611440e9b3aafedbd63863c3cda3ac272018eca45c14ad7ffe55"
        ),
        "grid_cells_sha256": (
            "766fe3130bbd4751801ae548699796781b82ad9609447661d44574e8f83fdb74"
        ),
        "accumulated_frame_schedule_sha256": (
            "09dce6c4e14b651d41424c3f8c9ee8636569ff6ae9baf6bf39e8a718fecfa83f"
        ),
        "fixture_sha256": (
            "ebafd1ef5f7f86cf55bb792dcf191c3c96fa8c8b02f6836cde7fba960385eac3"
        ),
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
        "max_total_operator_elements": 464,
        "max_total_candidate_tensor_elements": 232,
        "error_locations": [44, 43, 45, 58],
        "error_locations_sha256": (
            "8ca7d4324f754e978078fb971ca4775a1cff053e83f156e60a294f20ba9f8d96"
        ),
        "grid_cells_sha256": (
            "1091503728805c068cbb424b8fcc658a96793d732e9b6d0c537190b5333b9ada"
        ),
        "accumulated_frame_schedule_sha256": (
            "2d9ed4424fcaf62ae8f14fa17ed7f62d93aa4364207a654ba090fa2bc822ccc9"
        ),
        "fixture_sha256": (
            "727ec6d223a32a5d855df952a88abaa122ce0f20ce4c014af6a921396ea73f9a"
        ),
    },
}


def canonical_json_bytes(value: Any) -> bytes:
    """Return the exact canonical JSON encoding used by the fixture."""

    return (
        json.dumps(value, allow_nan=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def canonical_json_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _matrix_sha256(values: Sequence[complex]) -> str:
    """Hash row-major explicit-little-endian complex128 matrix entries."""

    payload = b"".join(
        struct.pack("<dd", float(complex(value).real), float(complex(value).imag))
        for value in values
    )
    return hashlib.sha256(payload).hexdigest()


_SQRT_HALF = 1.0 / math.sqrt(2.0)
H_MATRIX_SHA256 = _matrix_sha256(
    (_SQRT_HALF, _SQRT_HALF, _SQRT_HALF, -_SQRT_HALF)
)
CX_MATRIX_SHA256 = _matrix_sha256(
    (
        1,
        0,
        0,
        0,
        0,
        1,
        0,
        0,
        0,
        0,
        0,
        1,
        0,
        0,
        1,
        0,
    )
)
MATRIX_SHA256 = {"H": H_MATRIX_SHA256, "CX": CX_MATRIX_SHA256}


def preflight_output_paths(paths: Sequence[Path]) -> tuple[Path, ...]:
    """Resolve outputs and reject unsafe or replacing publication."""

    resolved: list[Path] = []
    for path_like in paths:
        path = Path(path_like)
        try:
            parent = path.parent.resolve(strict=True)
        except FileNotFoundError as error:
            raise FileNotFoundError(
                f"output parent directory does not exist: {path.parent}"
            ) from error
        if not parent.is_dir():
            raise NotADirectoryError(
                f"output parent is not a directory: {path.parent}"
            )
        resolved.append(parent / path.name)
    if len(set(resolved)) != len(resolved):
        raise ValueError("output paths must be pairwise distinct")
    existing = [str(path) for path in resolved if os.path.lexists(path)]
    if existing:
        raise FileExistsError(f"refusing to replace existing outputs: {existing}")
    return tuple(resolved)


def _publish_temporary_exclusive(temporary: Path, destination: Path) -> None:
    try:
        os.link(temporary, destination)
    except FileExistsError as error:
        raise FileExistsError(
            f"refusing to replace existing output: {destination}"
        ) from error
    directory_descriptor = os.open(destination.parent, os.O_RDONLY)
    try:
        os.fsync(directory_descriptor)
    finally:
        os.close(directory_descriptor)


def _atomic_write(path: Path, data: bytes) -> None:
    destination = preflight_output_paths((path,))[0]
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        dir=destination.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        _publish_temporary_exclusive(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def dense_xzzx_memory(
    stim: Any,
    *,
    distance: int,
) -> tuple[Any, dict[str, Any]]:
    """Build the compact two-round local-H-conjugated Stim circuit."""

    if distance not in SUPPORTED_DISTANCES:
        raise ValueError(
            f"unsupported distance {distance}; expected {SUPPORTED_DISTANCES}"
        )
    source = stim.Circuit.generated(
        "surface_code:rotated_memory_z",
        distance=distance,
        rounds=SOURCE_ROUNDS,
    ).flattened()
    coordinates = source.get_final_qubit_coordinates()
    active = sorted(coordinates)
    compact = {qubit: index for index, qubit in enumerate(active)}
    data = {
        qubit
        for qubit, xy in coordinates.items()
        if int(xy[0]) % 2 == 1 and int(xy[1]) % 2 == 1
    }
    hadamard_frame = {
        qubit
        for qubit in data
        if (int(coordinates[qubit][0]) + int(coordinates[qubit][1])) % 4 == 2
    }

    transformed = stim.Circuit()
    for instruction in source:
        name = instruction.name
        targets = instruction.targets_copy()
        arguments = instruction.gate_args_copy()
        if name == "R":
            for target in targets:
                transformed.append(
                    "RX" if target.value in hadamard_frame else "R",
                    [compact[target.value]],
                    arguments,
                )
        elif name == "M":
            for target in targets:
                transformed.append(
                    "MX" if target.value in hadamard_frame else "M",
                    [compact[target.value]],
                    arguments,
                )
        elif name == "CX":
            for control, target in zip(
                targets[::2],
                targets[1::2],
                strict=True,
            ):
                selected_data = next(
                    (
                        candidate.value
                        for candidate in (control, target)
                        if candidate.value in hadamard_frame
                    ),
                    None,
                )
                if selected_data is not None:
                    transformed.append("H", [compact[selected_data]])
                transformed.append(
                    "CX",
                    [compact[control.value], compact[target.value]],
                    arguments,
                )
                if selected_data is not None:
                    transformed.append("H", [compact[selected_data]])
        else:
            mapped = [
                compact[target.value] if target.is_qubit_target else target
                for target in targets
            ]
            transformed.append(name, mapped, arguments)

    metadata = {
        "active_sparse_qubit_ids": active,
        "compact": compact,
        "coordinates": coordinates,
    }
    return transformed, metadata


def _gate_stream_bytes(gates: Sequence[Mapping[str, Any]]) -> bytes:
    return "".join(
        f"{int(row['index']):04d}|{row['token']}|"
        f"{','.join(str(int(target)) for target in row['targets'])}\n"
        for row in gates
    ).encode("ascii")


def _edge_stream_bytes(edges: Sequence[Sequence[int]]) -> bytes:
    return "".join(f"{int(a)},{int(b)}\n" for a, b in edges).encode("ascii")


def _prefix_from_transformed(
    stim: Any,
    circuit: Any,
) -> tuple[list[dict[str, Any]], list[int], Any]:
    gates: list[dict[str, Any]] = []
    rx_initialized: list[int] = []
    prefix_stim = stim.Circuit()
    found_first_mr = False

    def append_gate(token: str, targets: Sequence[int]) -> None:
        row = {
            "index": len(gates),
            "token": token,
            "targets": [int(target) for target in targets],
            "matrix_sha256": MATRIX_SHA256[token],
        }
        gates.append(row)
        prefix_stim.append(token, row["targets"])

    for instruction in circuit:
        name = instruction.name
        targets = instruction.targets_copy()
        if name == "MR":
            found_first_mr = True
            break
        if name in {"QUBIT_COORDS", "SHIFT_COORDS", "TICK"}:
            continue
        if name == "R":
            continue
        if name == "RX":
            for target in targets:
                qubit = int(target.qubit_value)
                rx_initialized.append(qubit)
                append_gate("H", [qubit])
            continue
        if name == "H":
            for target in targets:
                append_gate("H", [int(target.qubit_value)])
            continue
        if name == "CX":
            for control, target in zip(
                targets[::2],
                targets[1::2],
                strict=True,
            ):
                append_gate(
                    "CX",
                    [int(control.qubit_value), int(target.qubit_value)],
                )
            continue
        raise ValueError(
            f"unsupported operation before first MR: {instruction.name}"
        )
    if not found_first_mr:
        raise ValueError("transformed source contains no MR")
    return gates, rx_initialized, prefix_stim


def _site_kind(x: int, y: int) -> str:
    if x % 2 == 1 and y % 2 == 1:
        return "data"
    if x % 2 == 0 and y % 2 == 0:
        return "check"
    raise ValueError(f"unclassified active site coordinate {(x, y)}")


def _rank_error_locations(
    *,
    distance: int,
    degree: Mapping[int, int],
    coordinate_by_qubit: Mapping[int, Sequence[int]],
) -> list[dict[str, Any]]:
    ranked = sorted(
        (qubit for qubit, value in degree.items() if value == 4),
        key=lambda qubit: (
            (coordinate_by_qubit[qubit][0] - distance) ** 2
            + (coordinate_by_qubit[qubit][1] - distance) ** 2,
            qubit,
        ),
    )
    if len(ranked) < 4:
        raise RuntimeError("fewer than four degree-four active error locations")
    rows = []
    for location_rank, target in enumerate(ranked[:4], start=1):
        x, y = coordinate_by_qubit[target]
        rows.append(
            {
                "location_rank": location_rank,
                "target": target,
                "kind": _site_kind(x, y),
                "xy": [x, y],
            }
        )
    return rows


def _accumulated_frame_schedule(
    stim: Any,
    *,
    distance: int,
    prefix_stim: Any,
    error_locations: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    accumulated = stim.Circuit()
    rows: list[dict[str, Any]] = []
    for layer in range(1, distance + 1):
        accumulated += prefix_stim
        inverse = stim.Tableau.from_circuit(accumulated).inverse()
        for location in error_locations:
            target = int(location["target"])
            signed_pullback = str(inverse.y_output(target))
            rows.append(
                {
                    "layer": layer,
                    "location_rank": int(location["location_rank"]),
                    "target": target,
                    "signed_pullback": signed_pullback,
                    "support": [
                        index
                        for index, pauli in enumerate(signed_pullback[1:])
                        if pauli != "_"
                    ],
                }
            )
    return {
        "frame_boundary": (
            "after applying the full frozen H/CX prefix for this layer and "
            "before applying the current layer physical RY rotations"
        ),
        "rows": rows,
        "schedule_sha256": canonical_json_sha256(rows),
    }


def _grid_cells(
    *,
    distance: int,
    prefix: Mapping[str, Any],
    error_locations: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    for role, layer_spec, noise_complexity, probability in GRID_ROLE_SPECS:
        round_layers = distance if layer_spec == "distance" else int(layer_spec)
        p_twirl = float(probability)
        theta = float(2.0 * math.asin(math.sqrt(p_twirl)))
        selected = [
            int(row["target"])
            for row in error_locations[:noise_complexity]
        ]
        operation_ledger: list[dict[str, Any]] = []
        for layer in range(1, round_layers + 1):
            operation_ledger.append(
                {
                    "operation_index": len(operation_ledger),
                    "layer": layer,
                    "kind": "clifford_prefix",
                    "prefix_gate_count": int(prefix["gate_count"]),
                    "prefix_gate_stream_sha256": prefix["gate_stream_sha256"],
                }
            )
            for location in error_locations[:noise_complexity]:
                operation_ledger.append(
                    {
                        "operation_index": len(operation_ledger),
                        "layer": layer,
                        "kind": "physical_ry",
                        "location_rank": int(location["location_rank"]),
                        "target": int(location["target"]),
                        "theta_radians": theta,
                        "theta_float64_hex": theta.hex(),
                    }
                )
        cells.append(
            {
                "cell_id": f"d{distance}-{role}",
                "role": role,
                "round_layers": round_layers,
                "noise_complexity": noise_complexity,
                "p_twirl": p_twirl,
                "p_twirl_float64_hex": p_twirl.hex(),
                "theta_radians": theta,
                "theta_float64_hex": theta.hex(),
                "selected_targets": selected,
                "prefix_application_count": round_layers,
                "rotation_count": round_layers * noise_complexity,
                "operation_ledger": operation_ledger,
            }
        )
    return cells


def _expected_multi_resource_limits(n_qubits: int) -> dict[str, int]:
    return {
        "max_local_operator_elements": 64,
        "max_total_operator_elements": 64 * n_qubits,
        "max_local_candidate_tensor_elements": 4_194_304,
        "max_total_candidate_tensor_elements": 16_777_216,
        "max_predicted_bond_dimension": 64,
        "max_routed_rank_product": 64,
        "max_total_bond_growth_product": 64,
        "expected_refactor_factor_product": 1,
    }


def _build_fixture(
    stim: Any,
    *,
    distance: int,
) -> tuple[Any, dict[str, Any]]:
    circuit, metadata = dense_xzzx_memory(stim, distance=distance)
    expected = EXPECTED[distance]
    transformed_sha256 = hashlib.sha256(
        str(circuit).encode("utf-8")
    ).hexdigest()
    if transformed_sha256 != expected["transformed_sha256"]:
        raise RuntimeError(
            "transformed Stim SHA drift for "
            f"d={distance}: {transformed_sha256} != "
            f"{expected['transformed_sha256']}"
        )

    gates, rx_initialized, prefix_stim = _prefix_from_transformed(stim, circuit)
    edges: list[list[int]] = []
    seen_edges: set[tuple[int, int]] = set()
    for row in gates:
        if row["token"] != "CX":
            continue
        edge = tuple(sorted(int(target) for target in row["targets"]))
        if edge not in seen_edges:
            seen_edges.add(edge)
            edges.append([edge[0], edge[1]])

    coordinate_map = []
    for original in metadata["active_sparse_qubit_ids"]:
        compact = metadata["compact"][original]
        xy_raw = metadata["coordinates"][original]
        x, y = (int(value) for value in xy_raw)
        coordinate_map.append(
            {
                "compact_qubit": compact,
                "original_stim_qubit": original,
                "xy": [x, y],
                "rotated_row_col": [
                    (x + y) // 2 - 1,
                    (x - y) // 2 + distance - 1,
                ],
            }
        )

    degree = {qubit: 0 for qubit in range(expected["n_qubits"])}
    for left, right in edges:
        degree[left] += 1
        degree[right] += 1
    coordinate_by_qubit = {
        row["compact_qubit"]: row["xy"] for row in coordinate_map
    }
    error_locations = _rank_error_locations(
        distance=distance,
        degree=degree,
        coordinate_by_qubit=coordinate_by_qubit,
    )
    if [row["target"] for row in error_locations] != expected["error_locations"]:
        raise RuntimeError("ordered degree-four error locations drifted")
    target = int(error_locations[0]["target"])
    if target not in rx_initialized:
        raise RuntimeError("center data target is not RX-initialized")

    pullback = str(
        stim.Tableau.from_circuit(prefix_stim).inverse().y_output(target)
    )
    support = [
        index for index, pauli in enumerate(pullback[1:]) if pauli != "_"
    ]
    routing_edges = [edge for edge in edges if target in edge]

    payload = {
        "schema": FIXTURE_SCHEMA,
        "fixture_id": f"gcapeps-d{distance}-unitary-prefix-v2",
        "claim_boundary": (
            "equal-status persistent unitary-layer performance fixture; "
            "no state truth, measurement, reset, Record, or scaling claim"
        ),
        "distance": distance,
        "n_qubits": expected["n_qubits"],
        "dtype": "complex128",
        "peps_settings": {
            "cutoff": 1e-12,
            "renorm": False,
            "gauge_smudge": 0.0,
            "equilibrate_every": None,
            "max_bond": None,
            "to_backend": None,
            "convert_eager": True,
        },
        "stim_source": {
            "generator": "surface_code:rotated_memory_z",
            "rounds": SOURCE_ROUNDS,
            "transformed_sha256": transformed_sha256,
            "first_measurement": "MR",
            "rx_initialized_compact_qubits": sorted(rx_initialized),
        },
        "coordinate_map": coordinate_map,
        "prefix": {
            "gates": gates,
            "h_count": sum(row["token"] == "H" for row in gates),
            "cx_count": sum(row["token"] == "CX" for row in gates),
            "gate_count": len(gates),
            "gate_stream_sha256": hashlib.sha256(
                _gate_stream_bytes(gates)
            ).hexdigest(),
            "prefix_stim_sha256": hashlib.sha256(
                str(prefix_stim).encode("utf-8")
            ).hexdigest(),
        },
        "graph": {
            "edges": edges,
            "edge_count": len(edges),
            "edge_stream_sha256": hashlib.sha256(
                _edge_stream_bytes(edges)
            ).hexdigest(),
        },
        "nonclifford": {
            "physical_pauli": "Y",
            "target": target,
            "angle_radians": ANGLE_RADIANS,
            "active_rank": 2,
            "signed_pullback": pullback,
            "support": support,
            "routing_edges": routing_edges,
        },
        "gcapeps_resource_expectations": {
            "max_local_operator_elements": 64,
            "max_total_operator_elements": 4 * expected["n_qubits"] + 76,
            "max_local_candidate_tensor_elements": 32,
            "max_total_candidate_tensor_elements": (
                2 * expected["n_qubits"] + 38
            ),
            "max_predicted_bond_dimension": 2,
            "max_routed_rank_product": 2,
            "max_total_bond_growth_product": 2,
            "expected_refactor_factor_product": 1,
        },
    }
    accumulated_frame_schedule = _accumulated_frame_schedule(
        stim,
        distance=distance,
        prefix_stim=prefix_stim,
        error_locations=error_locations,
    )
    expected_schedule_sha256 = expected[
        "accumulated_frame_schedule_sha256"
    ]
    if (
        expected_schedule_sha256
        and accumulated_frame_schedule["schedule_sha256"]
        != expected_schedule_sha256
    ):
        raise RuntimeError("accumulated frame schedule SHA drifted")
    grid_cells = _grid_cells(
        distance=distance,
        prefix=payload["prefix"],
        error_locations=error_locations,
    )
    payload.update(
        {
            "error_locations": error_locations,
            "error_locations_sha256": canonical_json_sha256(error_locations),
            "grid_cells": grid_cells,
            "grid_cells_sha256": canonical_json_sha256(grid_cells),
            "accumulated_frame_schedule": accumulated_frame_schedule,
            "gcapeps_multi_resource_limits": (
                _expected_multi_resource_limits(expected["n_qubits"])
            ),
        }
    )
    return circuit, payload


def _expected_resources(n_qubits: int) -> dict[str, int]:
    return {
        "max_local_operator_elements": 64,
        "max_total_operator_elements": 4 * n_qubits + 76,
        "max_local_candidate_tensor_elements": 32,
        "max_total_candidate_tensor_elements": 2 * n_qubits + 38,
        "max_predicted_bond_dimension": 2,
        "max_routed_rank_product": 2,
        "max_total_bond_growth_product": 2,
        "expected_refactor_factor_product": 1,
    }


def validate_fixture(fixture: Mapping[str, Any]) -> str:
    """Fail closed unless *fixture* is one exact preregistered object."""

    if fixture.get("schema") != FIXTURE_SCHEMA:
        raise ValueError(f"fixture schema must be {FIXTURE_SCHEMA!r}")
    distance = fixture.get("distance")
    if distance not in SUPPORTED_DISTANCES:
        raise ValueError(f"unsupported fixture distance: {distance!r}")
    expected = EXPECTED[int(distance)]
    n_qubits = expected["n_qubits"]
    if fixture.get("fixture_id") != f"gcapeps-d{distance}-unitary-prefix-v2":
        raise ValueError("fixture id mismatch")
    if fixture.get("n_qubits") != n_qubits or fixture.get("dtype") != "complex128":
        raise ValueError("fixture width or dtype mismatch")

    source = fixture.get("stim_source", {})
    if (
        source.get("generator") != "surface_code:rotated_memory_z"
        or source.get("rounds") != SOURCE_ROUNDS
        or source.get("first_measurement") != "MR"
        or source.get("transformed_sha256") != expected["transformed_sha256"]
    ):
        raise ValueError("Stim source contract mismatch")

    coordinates = fixture.get("coordinate_map", ())
    if [row.get("compact_qubit") for row in coordinates] != list(range(n_qubits)):
        raise ValueError("coordinate compact ids mismatch")
    originals = [row.get("original_stim_qubit") for row in coordinates]
    if originals != sorted(originals) or len(set(originals)) != n_qubits:
        raise ValueError("coordinate original Stim ids mismatch")
    rotated: list[tuple[int, int]] = []
    for row in coordinates:
        x, y = row.get("xy", (None, None))
        if not isinstance(x, int) or not isinstance(y, int):
            raise ValueError("physical coordinates must be integers")
        expected_rotated = [
            (x + y) // 2 - 1,
            (x - y) // 2 + int(distance) - 1,
        ]
        if (
            (x + y) % 2
            or (x - y) % 2
            or row.get("rotated_row_col") != expected_rotated
        ):
            raise ValueError("rotated coordinate formula mismatch")
        if not all(0 <= value <= 2 * int(distance) - 2 for value in expected_rotated):
            raise ValueError("rotated coordinate outside frozen bounds")
        rotated.append(tuple(expected_rotated))
    if len(set(rotated)) != n_qubits:
        raise ValueError("rotated coordinates are not unique")

    prefix = fixture.get("prefix", {})
    gates = prefix.get("gates", ())
    if [row.get("index") for row in gates] != list(range(expected["gate_count"])):
        raise ValueError("prefix gate indices mismatch")
    for row in gates:
        token = row.get("token")
        targets = row.get("targets")
        if (
            token not in MATRIX_SHA256
            or len(targets) != {"H": 1, "CX": 2}[token]
            or not all(
                isinstance(target, int) and 0 <= target < n_qubits
                for target in targets
            )
            or row.get("matrix_sha256") != MATRIX_SHA256[token]
        ):
            raise ValueError("prefix gate row or matrix hash mismatch")
    gate_stream_sha256 = hashlib.sha256(_gate_stream_bytes(gates)).hexdigest()
    if (
        prefix.get("h_count") != expected["h_count"]
        or prefix.get("cx_count") != expected["cx_count"]
        or prefix.get("gate_count") != expected["gate_count"]
        or prefix.get("gate_stream_sha256") != gate_stream_sha256
        or gate_stream_sha256 != expected["gate_stream_sha256"]
    ):
        raise ValueError("prefix gate stream mismatch")

    edges = fixture.get("graph", {}).get("edges", ())
    if any(
        len(edge) != 2
        or edge != sorted(edge)
        or edge[0] == edge[1]
        or not all(isinstance(qubit, int) and 0 <= qubit < n_qubits for qubit in edge)
        for edge in edges
    ):
        raise ValueError("graph edge row mismatch")
    if len({tuple(edge) for edge in edges}) != len(edges):
        raise ValueError("graph edges are not unique")
    graph = fixture.get("graph", {})
    edge_stream_sha256 = hashlib.sha256(_edge_stream_bytes(edges)).hexdigest()
    if (
        graph.get("edge_count") != expected["edge_count"]
        or graph.get("edge_count") != len(edges)
        or graph.get("edge_stream_sha256") != edge_stream_sha256
        or edge_stream_sha256 != expected["edge_stream_sha256"]
    ):
        raise ValueError("graph edge stream mismatch")
    by_compact = {row["compact_qubit"]: row for row in coordinates}
    for left, right in edges:
        lr = by_compact[left]["rotated_row_col"]
        rr = by_compact[right]["rotated_row_col"]
        if abs(lr[0] - rr[0]) + abs(lr[1] - rr[1]) != 1:
            raise ValueError(
                "graph edge is not nearest-neighbor in rotated coordinates"
            )

    nonclifford = fixture.get("nonclifford", {})
    if (
        nonclifford.get("physical_pauli") != "Y"
        or nonclifford.get("target") != expected["target"]
        or nonclifford.get("angle_radians") != ANGLE_RADIANS
        or nonclifford.get("active_rank") != 2
    ):
        raise ValueError("non-Clifford physical row mismatch")
    if nonclifford.get("signed_pullback") != expected["signed_pullback"]:
        raise ValueError("signed pullback mismatch")
    if nonclifford.get("support") != expected["support"]:
        raise ValueError("signed pullback support mismatch")
    target = expected["target"]
    incident = [edge for edge in edges if target in edge]
    if (
        len(incident) != 4
        or nonclifford.get("routing_edges") != incident
        or sorted({qubit for edge in incident for qubit in edge})
        != expected["support"]
    ):
        raise ValueError("non-Clifford routing edges are not the frozen four-edge star")
    if by_compact[target]["xy"] != expected["xy"]:
        raise ValueError("non-Clifford target coordinate mismatch")
    if target not in source.get("rx_initialized_compact_qubits", ()):
        raise ValueError("non-Clifford target is not RX-initialized")

    import stim

    prefix_circuit = stim.Circuit()
    for row in gates:
        prefix_circuit.append(row["token"], row["targets"])
    prefix_stim_sha256 = hashlib.sha256(
        str(prefix_circuit).encode("utf-8")
    ).hexdigest()
    if prefix.get("prefix_stim_sha256") != prefix_stim_sha256:
        raise ValueError("prefix Stim SHA mismatch")
    actual_pullback = str(
        stim.Tableau.from_circuit(prefix_circuit).inverse().y_output(target)
    )
    if actual_pullback != expected["signed_pullback"]:
        raise ValueError("Stim exact signed pullback mismatch")

    degree = {qubit: 0 for qubit in range(n_qubits)}
    for left, right in edges:
        degree[left] += 1
        degree[right] += 1
    coordinate_by_qubit = {
        row["compact_qubit"]: row["xy"] for row in coordinates
    }
    actual_error_locations = _rank_error_locations(
        distance=int(distance),
        degree=degree,
        coordinate_by_qubit=coordinate_by_qubit,
    )
    error_locations = fixture.get("error_locations")
    if error_locations != actual_error_locations:
        raise ValueError("ordered degree-four error locations mismatch")
    if [row["target"] for row in error_locations] != expected["error_locations"]:
        raise ValueError("frozen error-location targets mismatch")
    if (
        fixture.get("error_locations_sha256")
        != canonical_json_sha256(error_locations)
        or fixture.get("error_locations_sha256")
        != expected["error_locations_sha256"]
    ):
        raise ValueError("error-location SHA mismatch")

    expected_grid_cells = _grid_cells(
        distance=int(distance),
        prefix=prefix,
        error_locations=error_locations,
    )
    grid_cells = fixture.get("grid_cells")
    if grid_cells != expected_grid_cells:
        raise ValueError("grid cell or operation ledger mismatch")
    if (
        fixture.get("grid_cells_sha256") != canonical_json_sha256(grid_cells)
        or fixture.get("grid_cells_sha256") != expected["grid_cells_sha256"]
    ):
        raise ValueError("grid cells SHA mismatch")

    expected_schedule = _accumulated_frame_schedule(
        stim,
        distance=int(distance),
        prefix_stim=prefix_circuit,
        error_locations=error_locations,
    )
    schedule = fixture.get("accumulated_frame_schedule")
    if schedule != expected_schedule:
        raise ValueError("accumulated frame schedule or support mismatch")
    if (
        schedule["schedule_sha256"]
        != expected["accumulated_frame_schedule_sha256"]
    ):
        raise ValueError("accumulated frame schedule SHA mismatch")

    if fixture.get("gcapeps_multi_resource_limits") != (
        _expected_multi_resource_limits(n_qubits)
    ):
        raise ValueError("GCAPEPS multi-update hard guard mismatch")

    if fixture.get("gcapeps_resource_expectations") != _expected_resources(
        n_qubits
    ):
        raise ValueError("GCAPEPS resource expectations mismatch")
    if fixture.get("peps_settings") != {
        "cutoff": 1e-12,
        "renorm": False,
        "gauge_smudge": 0.0,
        "equilibrate_every": None,
        "max_bond": None,
        "to_backend": None,
        "convert_eager": True,
    }:
        raise ValueError("PEPS numerical settings mismatch")

    digest = canonical_json_sha256(fixture)
    expected_digest = expected["fixture_sha256"]
    if expected_digest and digest != expected_digest:
        raise ValueError(
            f"canonical fixture SHA mismatch: {digest} != {expected_digest}"
        )
    return digest


def emit_fixture(
    stim: Any,
    *,
    distance: int,
) -> tuple[Any, dict[str, Any]]:
    """Build and validate one frozen neutral fixture."""

    circuit, fixture = _build_fixture(stim, distance=distance)
    validate_fixture(fixture)
    return circuit, fixture


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--distance",
        type=int,
        choices=SUPPORTED_DISTANCES,
        required=True,
    )
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-stim", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    args.output_json, args.output_stim = preflight_output_paths(
        (args.output_json, args.output_stim)
    )
    import stim

    circuit, fixture = emit_fixture(stim, distance=args.distance)
    _atomic_write(args.output_json, canonical_json_bytes(fixture))
    _atomic_write(args.output_stim, str(circuit).encode("utf-8"))
    print(
        f"gcapeps d={args.distance} first-MR prefix: "
        f"qubits={fixture['n_qubits']} "
        f"gates={fixture['prefix']['gate_count']} "
        f"fixture_sha256={canonical_json_sha256(fixture)}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

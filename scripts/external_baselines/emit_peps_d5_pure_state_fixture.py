#!/usr/bin/env python3
"""Emit the neutral d5 pure-state fixture for external PEPS comparisons.

The fixture is a deterministic four-cycle unitary circuit on a 5x5 open
square lattice.  A checkerboard local frame turns every nearest-neighbour
two-site rotation into an XZ or ZX rotation.  This is a state-fidelity
benchmark on the data-patch geometry, not a syndrome-extraction circuit or a
multi-time Record fixture.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any


FIXTURE_SCHEMA = (
    "error_coupling_simulator.external.peps_d5_pure_state_fixture.v1"
)
CYCLE_PARAMETERS = (
    ("0.17", "0.11"),
    ("0.23", "-0.07"),
    ("0.31", "0.13"),
    ("0.37", "-0.19"),
)
EXPECTED_CANONICAL_SHA256_BY_SIZE = {
    3: "d53a3cd27e53f3fcf5fbe8c0d91232d1f81e2f8d914d78bea6914ec3988c4125",
    5: "c73b932ff8c213d6dce956cddb9bee0c9bfa2b465bde3bc6a3ece5789aed1324",
}


def claim_boundary(size: int) -> str:
    return (
        f"controlled {size}x{size} pure-state unitary benchmark only; "
        "no ancilla, measurement, reset, Kraus, leakage, Record, LER, "
        "calibration, or scaling claim"
    )


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


def square_edges(size: int) -> list[dict[str, Any]]:
    if isinstance(size, bool) or not isinstance(size, int) or size < 2:
        raise ValueError("size must be an integer at least two")
    edges: list[dict[str, Any]] = []
    color_specs = (
        ("horizontal_even", "horizontal", 0),
        ("horizontal_odd", "horizontal", 1),
        ("vertical_even", "vertical", 0),
        ("vertical_odd", "vertical", 1),
    )
    for color, orientation, parity in color_specs:
        if orientation == "horizontal":
            for row in range(size):
                for column in range(size - 1):
                    if column % 2 != parity:
                        continue
                    a = size * row + column
                    b = a + 1
                    edges.append(
                        {
                            "a": a,
                            "b": b,
                            "color": color,
                            "orientation": orientation,
                        }
                    )
        else:
            for row in range(size - 1):
                if row % 2 != parity:
                    continue
                for column in range(size):
                    a = size * row + column
                    b = a + size
                    edges.append(
                        {
                            "a": a,
                            "b": b,
                            "color": color,
                            "orientation": orientation,
                        }
                    )
    return edges


def _build_fixture_payload(*, size: int) -> dict[str, Any]:
    if size not in {3, 5}:
        raise ValueError("only the frozen d3 control and d5 target are supported")
    site_count = size * size
    sites = [
        {
            "qubit": size * row + column,
            "row": row,
            "column": column,
            "frame_pauli": "X" if (row + column) % 2 == 0 else "Z",
        }
        for row in range(size)
        for column in range(size)
    ]
    edges = square_edges(size)
    operations: list[dict[str, Any]] = []

    # The Z-frame sublattice begins in |+>; all other sites remain in |0>.
    for site in sites:
        if site["frame_pauli"] == "Z":
            operations.append(
                {
                    "index": len(operations),
                    "kind": "H",
                    "targets": [site["qubit"]],
                    "stage": "initial_state",
                }
            )

    for cycle, (theta, phi) in enumerate(CYCLE_PARAMETERS):
        for edge in edges:
            a = edge["a"]
            b = edge["b"]
            paulis = [sites[a]["frame_pauli"], sites[b]["frame_pauli"]]
            if sorted(paulis) != ["X", "Z"]:
                raise RuntimeError("checkerboard edge did not receive X/Z frames")
            operations.append(
                {
                    "index": len(operations),
                    "kind": "PAULI_ROTATION",
                    "targets": [a, b],
                    "paulis": paulis,
                    "angle_rad": theta,
                    "cycle": cycle,
                    "edge_color": edge["color"],
                }
            )
        for site in sites:
            signed_phi = phi
            if (site["row"] + site["column"]) % 2 == 1:
                signed_phi = (
                    phi[1:] if phi.startswith("-") else f"-{phi}"
                )
            operations.append(
                {
                    "index": len(operations),
                    "kind": "RY",
                    "targets": [site["qubit"]],
                    "angle_rad": signed_phi,
                    "cycle": cycle,
                    "stage": "post_edge_layers",
                }
            )

    payload = {
        "schema": FIXTURE_SCHEMA,
        "family": "checkerboard_xz_coherent_square_lattice",
        "claim_boundary": claim_boundary(size),
        "distance_label": size,
        "lattice": {
            "rows": size,
            "columns": size,
            "boundary": "open",
            "site_order": "row_major_q_equals_columns_times_row_plus_column",
        },
        "site_count": site_count,
        "sites": sites,
        "edge_count": len(edges),
        "edges_in_execution_order": edges,
        "cycle_count": len(CYCLE_PARAMETERS),
        "cycle_parameters": [
            {
                "cycle": cycle,
                "theta_rad": theta,
                "phi_rad_before_checkerboard_sign": phi,
            }
            for cycle, (theta, phi) in enumerate(CYCLE_PARAMETERS)
        ],
        "operation_count": len(operations),
        "two_site_operation_count": sum(
            operation["kind"] == "PAULI_ROTATION"
            for operation in operations
        ),
        "one_site_operation_count": sum(
            operation["kind"] in {"H", "RY"} for operation in operations
        ),
        "exact_per_edge_bond_ceiling": 2 ** len(CYCLE_PARAMETERS),
        "dtype": "complex128",
        "amplitude_convention": {
            "storage": "one_dimensional_c_order_complex128",
            "qubit_axis_order": list(range(site_count)),
            "q0_axis": 0,
            "q0_bit_significance": "most_significant",
            "flat_index": (
                "sum_q bit(q)*2**(site_count-1-q)"
            ),
            "local_basis": ["|0>", "|1>"],
            "two_qubit_basis": ["|00>", "|01>", "|10>", "|11>"],
            "target_to_kronecker_factor": (
                "targets[0] is the left Kronecker factor and the more "
                "significant local basis bit"
            ),
            "matrix_indices": "row_is_output_column_is_input",
            "chronological_update": (
                "operations execute in ascending index; psi <- U_operation*psi; "
                "final_state=U_last*...*U_1*U_0*initial_state"
            ),
        },
        "serialization_convention": {
            "within_edge_color": (
                "horizontal edges use ascending row then left column; vertical "
                "edges use ascending top row then column"
            ),
            "parallelism": (
                "edges in one color are disjoint and may execute in parallel, "
                "but the canonical JSON serializes them in the declared order"
            ),
        },
        "gate_conventions": {
            "H": {
                "matrix": [
                    ["1/sqrt(2)", "1/sqrt(2)"],
                    ["1/sqrt(2)", "-1/sqrt(2)"],
                ],
            },
            "RY": {
                "definition": "exp(-i*angle_rad*Y/2)",
                "matrix": [
                    ["cos(angle_rad/2)", "-sin(angle_rad/2)"],
                    ["sin(angle_rad/2)", "cos(angle_rad/2)"],
                ],
            },
            "PAULI_ROTATION": {
                "definition": (
                    "exp(-i*angle_rad*(P_targets[0] tensor "
                    "P_targets[1])/2)"
                ),
                "closed_form": (
                    "cos(angle_rad/2)*I4 - "
                    "i*sin(angle_rad/2)*(P0 tensor P1)"
                ),
            },
        },
        "operations": operations,
    }
    return payload


def build_fixture(*, size: int = 5) -> dict[str, Any]:
    payload = _build_fixture_payload(size=size)
    validate_fixture(payload, expected_size=size, require_pinned_hash=False)
    return payload


def _semantic_mismatch(
    observed: Any,
    expected: Any,
    *,
    path: str = "fixture",
) -> str | None:
    if type(observed) is not type(expected):
        return (
            f"{path} type {type(observed).__name__} != "
            f"{type(expected).__name__}"
        )
    if isinstance(expected, dict):
        if set(observed) != set(expected):
            return (
                f"{path} keys {sorted(observed)} != {sorted(expected)}"
            )
        for key in expected:
            mismatch = _semantic_mismatch(
                observed[key],
                expected[key],
                path=f"{path}.{key}",
            )
            if mismatch is not None:
                return mismatch
        return None
    if isinstance(expected, list):
        if len(observed) != len(expected):
            return f"{path} length {len(observed)} != {len(expected)}"
        for index, expected_value in enumerate(expected):
            mismatch = _semantic_mismatch(
                observed[index],
                expected_value,
                path=f"{path}[{index}]",
            )
            if mismatch is not None:
                return mismatch
        return None
    if observed != expected:
        return f"{path} value {observed!r} != {expected!r}"
    return None


def validate_fixture(
    payload: Any,
    *,
    expected_size: int,
    require_pinned_hash: bool = True,
) -> str:
    if not isinstance(payload, dict):
        raise ValueError("fixture root must be an object")
    if payload.get("schema") != FIXTURE_SCHEMA:
        raise ValueError(f"unsupported fixture schema: {payload.get('schema')!r}")
    if payload.get("distance_label") != expected_size:
        raise ValueError("fixture distance label mismatch")
    if payload.get("site_count") != expected_size**2:
        raise ValueError("fixture site count mismatch")
    expected_edges = 2 * expected_size * (expected_size - 1)
    if payload.get("edge_count") != expected_edges:
        raise ValueError("fixture edge count mismatch")
    if payload.get("cycle_count") != len(CYCLE_PARAMETERS):
        raise ValueError("fixture cycle count mismatch")
    if payload.get("two_site_operation_count") != (
        len(CYCLE_PARAMETERS) * expected_edges
    ):
        raise ValueError("fixture two-site operation count mismatch")
    if payload.get("exact_per_edge_bond_ceiling") != 16:
        raise ValueError("fixture exact per-edge bond ceiling mismatch")
    operations = payload.get("operations")
    if not isinstance(operations, list) or not operations:
        raise ValueError("fixture operations must be a nonempty list")
    if payload.get("operation_count") != len(operations):
        raise ValueError("fixture operation count mismatch")
    allowed = {"H": 1, "RY": 1, "PAULI_ROTATION": 2}
    for index, operation in enumerate(operations):
        if not isinstance(operation, dict) or operation.get("index") != index:
            raise ValueError(f"fixture operation {index} identity mismatch")
        kind = operation.get("kind")
        targets = operation.get("targets")
        if kind not in allowed:
            raise ValueError(f"unsupported fixture operation kind: {kind!r}")
        if (
            not isinstance(targets, list)
            or len(targets) != allowed[kind]
            or len(set(targets)) != len(targets)
            or any(
                isinstance(target, bool)
                or not isinstance(target, int)
                or not 0 <= target < expected_size**2
                for target in targets
            )
        ):
            raise ValueError(f"invalid targets at operation {index}")
        if kind == "PAULI_ROTATION":
            if sorted(operation.get("paulis", [])) != ["X", "Z"]:
                raise ValueError(f"invalid Pauli pair at operation {index}")
            if operation.get("edge_color") not in {
                "horizontal_even",
                "horizontal_odd",
                "vertical_even",
                "vertical_odd",
            }:
                raise ValueError(f"invalid edge color at operation {index}")
        if kind in {"RY", "PAULI_ROTATION"}:
            try:
                angle = float(operation["angle_rad"])
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(
                    f"invalid angle at operation {index}"
                ) from error
            if not angle or not (-1.0 < angle < 1.0):
                raise ValueError(f"angle out of frozen range at operation {index}")

    semantic_mismatch = _semantic_mismatch(
        payload,
        _build_fixture_payload(size=expected_size),
    )
    if semantic_mismatch is not None:
        raise ValueError(f"fixture semantic mismatch: {semantic_mismatch}")

    fingerprint = canonical_sha256(payload)
    expected_fingerprint = EXPECTED_CANONICAL_SHA256_BY_SIZE[expected_size]
    if require_pinned_hash and fingerprint != expected_fingerprint:
        raise ValueError(
            f"d{expected_size} fixture fingerprint mismatch: {fingerprint} != "
            f"{expected_fingerprint}"
        )
    return fingerprint


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--distance", type=int, choices=(3, 5), required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    payload = build_fixture(size=args.distance)
    fingerprint = validate_fixture(
        payload,
        expected_size=args.distance,
        require_pinned_hash=True,
    )
    _atomic_write(
        args.output_json,
        (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    print(
        f"peps d={args.distance}: sites={payload['site_count']} "
        f"edges={payload['edge_count']} operations={payload['operation_count']} "
        f"two_site={payload['two_site_operation_count']} "
        f"exact_bond_ceiling={payload['exact_per_edge_bond_ceiling']} "
        f"canonical_sha256={fingerprint}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

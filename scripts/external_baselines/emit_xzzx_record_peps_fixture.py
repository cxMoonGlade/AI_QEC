#!/usr/bin/env python3
"""Emit hash-bound d=2/3/5 XZZX fixtures for the PEPS Record experiment.

The source circuit is Stim's noiseless rotated-surface-code Z memory.  A local
Hadamard frame on checkerboard data sites turns its CSS extraction shell into
the XZZX shell used by the frozen preregistration.  The output is deliberately
runtime-neutral: gates, measurement columns, reset flags, and ragged absolute
XOR rows are all explicit JSON.

This is an all-qubit engineering fixture.  It contains no leakage channel,
physical calibration, decoder claim, or finite-bond faithfulness claim.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping, Sequence


FIXTURE_SCHEMA = "error_coupling_simulator.external_xzzx_record_peps.fixture.v1"
ENUMERATION_SPEC_SCHEMA = (
    "error_coupling_simulator.external_xzzx_record_peps.enumeration_spec.v1"
)
RUN_SPEC_SCHEMA = (
    "error_coupling_simulator.external_xzzx_record_peps.run_spec.v2"
)
LEGACY_V1_RUN_SPEC_SCHEMA = (
    "error_coupling_simulator.external_xzzx_record_peps.run_spec.v1"
)
SUPPORTED_DISTANCES = (2, 3, 5)
SUPPORTED_ROUNDS = 2
EXPECTED = {
    2: {
        "shape": (7, 10, 5, 1),
        "operations": 57,
        "resets": 6,
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
        "detector_arities": {1: 4, 2: 8, 3: 2, 5: 2},
        "observable_arities": [3],
        "stim_sha256": (
            "7067b1241251bd7558e7dc85b2f84bc13a45c1217a49f8fcfa2e51205879ecb0"
        ),
        "fixture_sha256": (
            "3b2bf7d81f7241e0a3b6abb14c76474c362e696cf374c55e20e3d121946bbf3c"
        ),
        "seed": 2026072603,
        "run_spec_sha256": (
            "7dfa0a8ef9620712e6ea190aeda651c681295f9841963ce77686640255cc22a9"
        ),
        "legacy_v1_run_spec_sha256": (
            "11e86c8d205899d51440a7fab32dc31f046e723a047c4c7bc8fe9fed3f7e15b9"
        ),
    },
    5: {
        "shape": (49, 73, 48, 1),
        "operations": 490,
        "resets": 48,
        "detector_arities": {1: 12, 2: 24, 3: 4, 5: 8},
        "observable_arities": [5],
        "stim_sha256": (
            "be26b8708efe36a027bcf79074bc936de552b1a5d22b35b627d7d9cdbb27f008"
        ),
        "fixture_sha256": (
            "659fda875a91f2a6e3c64f8f03487b5a431edecb9849dd897bf2e6f390583495"
        ),
        "seed": 2026072605,
        "run_spec_sha256": (
            "06151ea1244495475259d40bf6ca7ad16cbdaf5f8184ee61b344fb2e81b413a4"
        ),
        "legacy_v1_run_spec_sha256": (
            "092353542f2e9e329f4d3ed735d0e6a10caa88bc048478ee15cc06aefc60ef23"
        ),
    },
}
ENUMERATION_SPEC_SHA256 = (
    "02aef76a65383fbfec9a2f3e0b62a7dd0691a574ee739a4b6b33326ba13681ca"
)


def canonical_json_bytes(value: Any) -> bytes:
    """Return the exact pretty canonical encoding fixed by preregistration."""

    return (
        json.dumps(
            value,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def canonical_json_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def preflight_output_paths(paths: Sequence[Path]) -> tuple[Path, ...]:
    """Resolve output paths and fail before work if publication is unsafe."""

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
    """Atomically publish one same-filesystem temporary without replacement."""

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
    rounds: int,
) -> tuple[Any, dict[str, Any]]:
    """Build the compact, local-H-conjugated Stim memory circuit."""

    if distance not in SUPPORTED_DISTANCES:
        raise ValueError(
            f"unsupported distance {distance}; expected one of {SUPPORTED_DISTANCES}"
        )
    if rounds != SUPPORTED_ROUNDS:
        raise ValueError(f"this frozen family requires rounds=2, got {rounds}")

    source = stim.Circuit.generated(
        "surface_code:rotated_memory_z",
        distance=distance,
        rounds=rounds,
    ).flattened()
    coordinates = source.get_final_qubit_coordinates()
    active = sorted(coordinates)
    dense = {qubit: index for index, qubit in enumerate(active)}
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
                    [dense[target.value]],
                    arguments,
                )
        elif name == "M":
            for target in targets:
                transformed.append(
                    "MX" if target.value in hadamard_frame else "M",
                    [dense[target.value]],
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
                    transformed.append("H", [dense[selected_data]])
                transformed.append(
                    "CX",
                    [dense[control.value], dense[target.value]],
                    arguments,
                )
                if selected_data is not None:
                    transformed.append("H", [dense[selected_data]])
        else:
            mapped = [
                dense[target.value] if target.is_qubit_target else target
                for target in targets
            ]
            transformed.append(name, mapped, arguments)

    frame = {
        "source_sparse_num_qubits": source.num_qubits,
        "active_sparse_qubit_ids": active,
        "dense_qubit_map": {str(qubit): dense[qubit] for qubit in active},
        "data_qubits": sorted(dense[qubit] for qubit in data),
        "hadamard_frame_data_qubits": sorted(
            dense[qubit] for qubit in hadamard_frame
        ),
        "coordinates": {
            str(dense[qubit]): [float(value) for value in coordinates[qubit]]
            for qubit in active
        },
    }
    return transformed, frame


def neutral_fixture(
    circuit: Any,
    frame: Mapping[str, Any],
    *,
    distance: int,
    rounds: int,
) -> dict[str, Any]:
    """Flatten the transformed Stim circuit into the frozen neutral schema."""

    operations: list[dict[str, Any]] = []
    detector_rows: list[list[int]] = []
    observable_rows: dict[int, list[int]] = {}
    measurement_order: list[dict[str, Any]] = []
    measurement_count = 0

    for instruction in circuit:
        name = instruction.name
        targets = instruction.targets_copy()
        if name in {"QUBIT_COORDS", "SHIFT_COORDS", "TICK"}:
            continue
        if name == "DETECTOR":
            detector_rows.append(
                [measurement_count + int(target.value) for target in targets]
            )
            continue
        if name == "OBSERVABLE_INCLUDE":
            observable = int(instruction.gate_args_copy()[0])
            observable_rows.setdefault(observable, []).extend(
                measurement_count + int(target.value) for target in targets
            )
            continue
        if name in {"R", "RX", "H", "M", "MX", "MR"}:
            for target in targets:
                qubit = int(target.qubit_value)
                operations.append({"op": name, "qubits": [qubit]})
                if name in {"M", "MX", "MR"}:
                    measurement_order.append(
                        {
                            "column": measurement_count,
                            "qubit": qubit,
                            "basis": "X" if name == "MX" else "Z",
                            "reset": name == "MR",
                        }
                    )
                    measurement_count += 1
            continue
        if name == "CX":
            for control, target in zip(
                targets[::2],
                targets[1::2],
                strict=True,
            ):
                operations.append(
                    {
                        "op": "CX",
                        "qubits": [
                            int(control.qubit_value),
                            int(target.qubit_value),
                        ],
                    }
                )
            continue
        raise ValueError(f"unsupported transformed Stim operation: {name}")

    ordered_observables = [
        observable_rows[index] for index in sorted(observable_rows)
    ]
    fingerprint = hashlib.sha256(str(circuit).encode("utf-8")).hexdigest()
    return {
        "schema": FIXTURE_SCHEMA,
        "family": "rotated_xzzx_memory_z_local_h",
        "claim_boundary": (
            "engineering capability fixture only; no calibration or finite-bond "
            "faithfulness claim"
        ),
        "distance": distance,
        "rounds": rounds,
        "num_qubits": circuit.num_qubits,
        "num_measurements": measurement_count,
        "num_detectors": len(detector_rows),
        "num_observables": len(ordered_observables),
        "stim_circuit_sha256": fingerprint,
        "frame": dict(frame),
        "operations": operations,
        "measurement_order": measurement_order,
        "detector_rows": detector_rows,
        "observable_rows": ordered_observables,
    }


def _intervention() -> dict[str, Any]:
    return {
        "after_rounds": [0, 1],
        "angle_radians": 0.02,
        "gate": "RY",
        "placement": (
            "after_each_complete_syndrome_round_before_the_next_base_operation"
        ),
        "targets": "all_data_qubits_in_ascending_dense_id_order",
    }


def enumeration_spec(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Return the exact d=2 full-law enumeration specification."""

    fixture_sha256 = validate_fixture(fixture)
    if fixture["distance"] != 2:
        raise ValueError("enumeration spec is defined only for distance=2")
    payload = {
        "base_fixture_sha256": fixture_sha256,
        "distance": 2,
        "intervention": _intervention(),
        "reference": {
            "method": "dense_complete_enumeration",
            "raw_outcome_count": 10,
            "support_size": 1024,
        },
        "rounds": 2,
        "schema": ENUMERATION_SPEC_SCHEMA,
        "stim_circuit_sha256": fixture["stim_circuit_sha256"],
    }
    digest = canonical_json_sha256(payload)
    if digest != ENUMERATION_SPEC_SHA256:
        raise RuntimeError(
            f"enumeration-spec drift: {digest} != {ENUMERATION_SPEC_SHA256}"
        )
    return payload


def run_spec(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Return the formal exact-data d=3 or d=5 v2 run specification."""

    fixture_sha256 = validate_fixture(fixture)
    distance = int(fixture["distance"])
    if distance not in {3, 5}:
        raise ValueError("run spec is defined only for distance 3 or 5")
    expected = EXPECTED[distance]
    payload = {
        "base_fixture_sha256": fixture_sha256,
        "distance": distance,
        "intervention": _intervention(),
        "reference_branch": {
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
                "seed": expected["seed"],
                "seed_encoding": "uint64_big_endian",
            },
            "shots": 1,
        },
        "reference_state": {
            "checkpoint": (
                "after_round_1_ry_before_terminal_data_measurements"
            ),
            "method": "numpy_exact_data_projector",
            "probability_floor": None,
            "truncation": None,
        },
        "rounds": 2,
        "schema": RUN_SPEC_SCHEMA,
        "stim_circuit_sha256": fixture["stim_circuit_sha256"],
    }
    digest = canonical_json_sha256(payload)
    if digest != expected["run_spec_sha256"]:
        raise RuntimeError(
            "run-spec drift for "
            f"distance={distance}: {digest} != {expected['run_spec_sha256']}"
        )
    return payload


def legacy_v1_run_spec(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Rebuild the killed v1 identity for regression only, never formal use."""

    fixture_sha256 = validate_fixture(fixture)
    distance = int(fixture["distance"])
    if distance not in {3, 5}:
        raise ValueError("legacy v1 run spec exists only for distance 3 or 5")
    expected = EXPECTED[distance]
    payload = {
        "base_fixture_sha256": fixture_sha256,
        "distance": distance,
        "intervention": _intervention(),
        "reference_branch": {
            "sampler": "qiskit_aer_matrix_product_state",
            "seed_simulator": expected["seed"],
            "shots": 1,
        },
        "rounds": 2,
        "schema": LEGACY_V1_RUN_SPEC_SCHEMA,
        "stim_circuit_sha256": fixture["stim_circuit_sha256"],
    }
    digest = canonical_json_sha256(payload)
    if digest != expected["legacy_v1_run_spec_sha256"]:
        raise RuntimeError(
            "legacy v1 run-spec regression drift for "
            f"distance={distance}: {digest} != "
            f"{expected['legacy_v1_run_spec_sha256']}"
        )
    return payload


def validate_fixture(fixture: Mapping[str, Any]) -> str:
    """Fail closed unless a fixture is exactly one frozen canonical object."""

    if fixture.get("schema") != FIXTURE_SCHEMA:
        raise ValueError(f"fixture schema must be {FIXTURE_SCHEMA!r}")
    distance = fixture.get("distance")
    if distance not in SUPPORTED_DISTANCES:
        raise ValueError(f"unsupported fixture distance: {distance!r}")
    expected = EXPECTED[int(distance)]
    digest = canonical_json_sha256(fixture)
    if digest != expected["fixture_sha256"]:
        raise ValueError(
            "canonical fixture SHA mismatch for "
            f"distance={distance}: {digest} != {expected['fixture_sha256']}"
        )
    observed_shape = (
        fixture.get("num_qubits"),
        fixture.get("num_measurements"),
        fixture.get("num_detectors"),
        fixture.get("num_observables"),
    )
    if observed_shape != expected["shape"]:
        raise ValueError(
            f"fixture shape mismatch: {observed_shape} != {expected['shape']}"
        )
    if len(fixture.get("operations", ())) != expected["operations"]:
        raise ValueError("fixture operation count mismatch")
    if fixture.get("stim_circuit_sha256") != expected["stim_sha256"]:
        raise ValueError("transformed Stim SHA mismatch")
    if Counter(map(len, fixture.get("detector_rows", ()))) != expected[
        "detector_arities"
    ]:
        raise ValueError("fixture detector arities mismatch")
    if list(map(len, fixture.get("observable_rows", ()))) != expected[
        "observable_arities"
    ]:
        raise ValueError("fixture observable arities mismatch")
    measurement_order = fixture.get("measurement_order", ())
    if [row.get("column") for row in measurement_order] != list(
        range(expected["shape"][1])
    ):
        raise ValueError("fixture measurement columns are not absolute and ordered")
    if sum(bool(row.get("reset")) for row in measurement_order) != expected[
        "resets"
    ]:
        raise ValueError("fixture reset count mismatch")
    return digest


def validate_run_spec(
    spec: Mapping[str, Any],
    fixture: Mapping[str, Any],
) -> str:
    """Validate exact equality with the spec derived from a frozen fixture."""

    expected_spec = (
        enumeration_spec(fixture)
        if fixture["distance"] == 2
        else run_spec(fixture)
    )
    if dict(spec) != expected_spec:
        raise ValueError("run/enumeration spec does not match the frozen fixture")
    return canonical_json_sha256(spec)


def emit_fixture(
    stim: Any,
    *,
    distance: int,
    rounds: int = SUPPORTED_ROUNDS,
) -> tuple[Any, dict[str, Any]]:
    """Build and validate one frozen fixture."""

    circuit, frame = dense_xzzx_memory(
        stim,
        distance=distance,
        rounds=rounds,
    )
    fixture = neutral_fixture(
        circuit,
        frame,
        distance=distance,
        rounds=rounds,
    )
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
    parser.add_argument("--rounds", type=int, choices=[2], default=2)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-stim", type=Path, required=True)
    parser.add_argument(
        "--output-spec",
        type=Path,
        help="optional enumeration spec (d2) or run spec (d3/d5)",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    output_paths = [args.output_json, args.output_stim]
    if args.output_spec is not None:
        output_paths.append(args.output_spec)
    (
        args.output_json,
        args.output_stim,
        *optional_spec,
    ) = preflight_output_paths(output_paths)
    args.output_spec = optional_spec[0] if optional_spec else None
    import stim

    circuit, fixture = emit_fixture(
        stim,
        distance=args.distance,
        rounds=args.rounds,
    )
    _atomic_write(args.output_json, canonical_json_bytes(fixture))
    _atomic_write(args.output_stim, str(circuit).encode("utf-8"))
    if args.output_spec is not None:
        spec = (
            enumeration_spec(fixture)
            if args.distance == 2
            else run_spec(fixture)
        )
        _atomic_write(args.output_spec, canonical_json_bytes(spec))
    print(
        f"xzzx d={args.distance} rounds=2: "
        f"qubits={fixture['num_qubits']} "
        f"measurements={fixture['num_measurements']} "
        f"detectors={fixture['num_detectors']} "
        f"stim_sha256={fixture['stim_circuit_sha256']} "
        f"fixture_sha256={canonical_json_sha256(fixture)}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Emit the neutral XZZX d=7 capability fixture used by external probes.

The source is Stim's noiseless rotated-surface-code Z-memory circuit.  A local
Hadamard frame on checkerboard data sites turns every bulk CSS check into an
``XZZX`` check.  This script performs that conjugation gate by gate, compacts
Stim's sparse qubit ids, and writes:

* the transformed Stim circuit, which is independently sampleable; and
* neutral JSON with explicit operations and absolute detector/observable XOR
  rows for runtimes that do not understand Stim annotations.

This is an engineering fixture.  It supplies no physical calibration and makes
no claim that a finite-bond execution is faithful.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any


FIXTURE_SCHEMA = "error_coupling_simulator.external_xzzx_d7.fixture.v1"
EXPECTED_FINGERPRINTS = {
    2: "193d56d199b45016d91e8d5742f52fdc4e8e3b74d571891c78e28f7ec4eca6bd",
    7: "20a32d1cd1293d4d4d6e74d8af04fe7b1300ddb82dbf734f558fb764ad27c4d7",
}
EXPECTED_SHAPES = {
    2: (97, 145, 96, 1),
    7: (97, 385, 336, 1),
}


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
    finally:
        temporary.unlink(missing_ok=True)


def dense_xzzx_memory(stim: Any, *, distance: int, rounds: int) -> tuple[Any, dict[str, Any]]:
    """Return the dense local-H-conjugated memory circuit and frame metadata."""

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
            for control, target in zip(targets[::2], targets[1::2], strict=True):
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

    metadata = {
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
    return transformed, metadata


def neutral_fixture(circuit: Any, frame: dict[str, Any], *, rounds: int) -> dict[str, Any]:
    """Flatten a transformed Stim circuit into a runtime-neutral contract."""

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
            for control, target in zip(targets[::2], targets[1::2], strict=True):
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
    circuit_text = str(circuit)
    fingerprint = hashlib.sha256(circuit_text.encode("utf-8")).hexdigest()
    payload = {
        "schema": FIXTURE_SCHEMA,
        "family": "rotated_xzzx_memory_z_local_h",
        "claim_boundary": (
            "engineering capability fixture only; no calibration or finite-bond "
            "faithfulness claim"
        ),
        "distance": 7,
        "rounds": rounds,
        "num_qubits": circuit.num_qubits,
        "num_measurements": measurement_count,
        "num_detectors": len(detector_rows),
        "num_observables": len(ordered_observables),
        "stim_circuit_sha256": fingerprint,
        "frame": frame,
        "operations": operations,
        "measurement_order": measurement_order,
        "detector_rows": detector_rows,
        "observable_rows": ordered_observables,
    }
    expected = EXPECTED_SHAPES.get(rounds)
    observed = (
        payload["num_qubits"],
        payload["num_measurements"],
        payload["num_detectors"],
        payload["num_observables"],
    )
    if expected is not None and observed != expected:
        raise RuntimeError(
            f"fixture shape drift for rounds={rounds}: {observed} != {expected}"
        )
    expected_fingerprint = EXPECTED_FINGERPRINTS.get(rounds)
    if expected_fingerprint is not None and fingerprint != expected_fingerprint:
        raise RuntimeError(
            "transformed Stim fingerprint drift for "
            f"rounds={rounds}: {fingerprint} != {expected_fingerprint}"
        )
    return payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds", type=int, choices=sorted(EXPECTED_SHAPES), required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-stim", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    import stim

    circuit, frame = dense_xzzx_memory(stim, distance=7, rounds=args.rounds)
    fixture = neutral_fixture(circuit, frame, rounds=args.rounds)
    _atomic_write(
        args.output_json,
        (json.dumps(fixture, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    _atomic_write(args.output_stim, str(circuit).encode("utf-8"))
    print(
        f"xzzx d=7 rounds={args.rounds}: qubits={fixture['num_qubits']} "
        f"measurements={fixture['num_measurements']} "
        f"detectors={fixture['num_detectors']} "
        f"sha256={fixture['stim_circuit_sha256']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

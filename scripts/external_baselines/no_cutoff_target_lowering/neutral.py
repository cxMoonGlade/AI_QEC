"""Lower the frozen Stim scaffold into one route-neutral Record program."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from scripts.external_baselines.no_cutoff_structure_census import (
    build_shadow_bundle,
)

from .model import (
    NEUTRAL_SCHEMA,
    STATIC_SCOPE,
    StaticArtifact,
    canonical_json_bytes,
    reject_floats,
    sha256_json,
)


REPO = Path(__file__).resolve().parents[3]
FIXTURE_PATH = (
    REPO
    / "docs"
    / "simulator_validation"
    / "NO_CUTOFF_STRUCTURE_CENSUS_FIXTURE_MANIFEST_2026-08-03.json"
)
FIXTURE_SHA256 = (
    "40474ca0beab8341d53bfa41da5438e052744bb83ae6af2632e1bfe273c53c74"
)
FIXTURE_SCHEMA = (
    "error_coupling_simulator.external.no_cutoff_structure_fixture_identity.v1"
)
GRID = {(distance, rounds) for distance in (3, 5) for rounds in (1, 3, 5, 7)}
_FORBIDDEN_KEYS = {
    "selected_sign",
    "current_root",
    "frontier",
    "probability",
    "solver_state",
}

_KIND = {
    "R": "RESET",
    "H": "H",
    "M": "M",
    "MR": "MR",
}
_KERNEL = {
    "COORD_MARKER": "MARKER_IDENTITY",
    "TICK_MARKER": "MARKER_IDENTITY",
    "RESET": "RESET_PAULI_INSTRUMENT",
    "H": "CLIFFORD_H",
    "CX": "CLIFFORD_CX",
    "COHERENT_Z": "PERSISTENT_COHERENT_Z",
    "M": "MEASURE_Z_INSTRUMENT",
    "MR": "MEASURE_RESET_Z_INSTRUMENT",
    "DETECTOR_APPEND": "DETECTOR_XOR_APPEND",
    "OBSERVABLE_XOR": "OBSERVABLE_XOR_ACCUMULATE",
    "FINALIZE_RECORD": "FINALIZE_OBSERVABLE_ZERO",
}


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _arg_strings(instruction: Any) -> list[str]:
    return [format(float(value), ".17g") for value in instruction.gate_args_copy()]


def _qubit_ref(target: Any, dense: dict[int, int]) -> dict[str, int]:
    if not target.is_qubit_target:
        raise ValueError("quantum operation has a non-qubit target")
    stim_id = int(target.value)
    if stim_id not in dense:
        raise ValueError(f"operation targets undeclared qubit {stim_id}")
    return {"stim_id": stim_id, "dense_ordinal": dense[stim_id]}


def _event(
    *,
    ordinal: int,
    kind: str,
    source_instruction: int | None,
    source_gate: str,
    source_target_ordinal: int | None = None,
    source_operand_ordinal: int | None = None,
    qubits: list[dict[str, int]] | None = None,
    args: list[str] | None = None,
    raw_output: int | None = None,
    rec_operands: list[dict[str, int]] | None = None,
    record_output: dict[str, int] | None = None,
) -> dict[str, Any]:
    return {
        "event_id": f"e{ordinal:06d}",
        "kind": kind,
        "source_instruction": source_instruction,
        "source_gate": source_gate,
        "source_target_ordinal": source_target_ordinal,
        "source_operand_ordinal": source_operand_ordinal,
        "qubits": [] if qubits is None else qubits,
        "args": [] if args is None else args,
        "raw_output": raw_output,
        "rec_operands": [] if rec_operands is None else rec_operands,
        "record_output": record_output,
        "kernel_id": _KERNEL[kind],
    }


def _manifest() -> dict[str, Any]:
    raw = FIXTURE_PATH.read_bytes()
    if _sha256(raw) != FIXTURE_SHA256:
        raise ValueError("frozen fixture manifest hash mismatch")
    value = json.loads(raw)
    if value.get("_schema") != FIXTURE_SCHEMA:
        raise ValueError("frozen fixture manifest schema mismatch")
    return value


def _reject_forbidden_keys(value: object, *, path: str = "artifact") -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in _FORBIDDEN_KEYS:
                raise ValueError(f"forbidden evaluator/solver field {key!r} at {path}")
            _reject_forbidden_keys(nested, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _reject_forbidden_keys(nested, path=f"{path}[{index}]")


def _validate_record_boundary_schema(semantic: dict[str, Any]) -> None:
    record = semantic.get("record_schema")
    if not isinstance(record, dict) or set(record) != {
        "raw_measurement_count",
        "detector_count",
        "observable_indices",
        "outputs",
        "record_width",
    }:
        raise ValueError("Record schema has missing or unknown fields")
    detector_count = record["detector_count"]
    outputs = record["outputs"]
    if (
        type(detector_count) is not int
        or detector_count < 0
        or not isinstance(outputs, list)
        or type(record["record_width"]) is not int
    ):
        raise ValueError("Record schema counts or outputs are invalid")
    expected_tags = [
        {"kind": "DETECTOR", "ordinal": ordinal}
        for ordinal in range(detector_count)
    ] + [{"kind": "OBSERVABLE", "ordinal": 0}]
    observed_tags: list[dict[str, Any]] = []
    for output in outputs:
        if not isinstance(output, dict) or set(output) != {
            "kind",
            "ordinal",
            "producer_event_id",
        }:
            raise ValueError("Record schema output row is invalid")
        if output["kind"] not in {"DETECTOR", "OBSERVABLE"}:
            raise ValueError("Record schema cannot expose raw or latent values")
        observed_tags.append(
            {"kind": output["kind"], "ordinal": output["ordinal"]}
        )
    if (
        observed_tags != expected_tags
        or record["observable_indices"] != [0]
        or record["record_width"] != len(outputs)
        or record["record_width"] != detector_count + 1
    ):
        raise ValueError("Record schema order or boundary width is invalid")


def _cell_identity(
    manifest: dict[str, Any], *, distance: int, rounds: int
) -> dict[str, Any]:
    matches = [
        cell
        for cell in manifest["cells"]
        if cell["distance"] == distance and cell["rounds"] == rounds
    ]
    if len(matches) != 1:
        raise ValueError("fixture manifest does not contain exactly one target cell")
    return dict(matches[0])


def lower_frozen_declared_error_record(
    *, distance: Literal[3, 5], rounds: Literal[1, 3, 5, 7]
) -> StaticArtifact:
    """Return the immutable neutral program; never execute a solver route."""

    if type(distance) is not int or type(rounds) is not int:
        raise TypeError("distance and rounds must be integers")
    if (distance, rounds) not in GRID:
        raise ValueError("cell is outside the frozen d={3,5}, R={1,3,5,7} grid")

    manifest = _manifest()
    frozen_cell = _cell_identity(manifest, distance=distance, rounds=rounds)
    bundle = build_shadow_bundle(distance=distance, rounds=rounds)
    if bundle["identity"] != frozen_cell:
        raise ValueError("generated Stim source/site map does not match frozen cell")

    source_text = str(bundle["source_text"])
    import stim

    circuit = stim.Circuit(source_text).flattened()
    qubits: list[dict[str, Any]] = []
    dense: dict[int, int] = {}
    for instruction in circuit:
        if instruction.name != "QUBIT_COORDS":
            continue
        targets = instruction.targets_copy()
        if len(targets) != 1 or not targets[0].is_qubit_target:
            raise ValueError("QUBIT_COORDS must declare one qubit")
        stim_id = int(targets[0].value)
        if stim_id in dense:
            raise ValueError(f"duplicate declared qubit {stim_id}")
        dense[stim_id] = len(qubits)
        qubits.append(
            {
                "stim_id": stim_id,
                "dense_ordinal": dense[stim_id],
                "coordinates": _arg_strings(instruction),
            }
        )

    events: list[dict[str, Any]] = []
    raw_count = 0
    detector_count = 0
    observable_indices: list[int] = []
    outputs: list[dict[str, Any]] = []

    def append(**kwargs: Any) -> dict[str, Any]:
        event = _event(ordinal=len(events), **kwargs)
        events.append(event)
        return event

    for source_index, instruction in enumerate(circuit):
        name = instruction.name
        targets = instruction.targets_copy()
        args = _arg_strings(instruction)
        if name == "QUBIT_COORDS":
            for target_index, target in enumerate(targets):
                append(
                    kind="COORD_MARKER",
                    source_instruction=source_index,
                    source_gate=name,
                    source_target_ordinal=target_index,
                    qubits=[_qubit_ref(target, dense)],
                    args=args,
                )
        elif name in _KIND:
            kind = _KIND[name]
            for target_index, target in enumerate(targets):
                raw_output = raw_count if name in {"M", "MR"} else None
                append(
                    kind=kind,
                    source_instruction=source_index,
                    source_gate=name,
                    source_target_ordinal=target_index,
                    qubits=[_qubit_ref(target, dense)],
                    args=args,
                    raw_output=raw_output,
                )
                if raw_output is not None:
                    raw_count += 1
        elif name == "CX":
            if len(targets) % 2:
                raise ValueError("CX target list must contain control-target pairs")
            for pair_index in range(0, len(targets), 2):
                append(
                    kind="CX",
                    source_instruction=source_index,
                    source_gate=name,
                    source_target_ordinal=pair_index // 2,
                    qubits=[
                        _qubit_ref(targets[pair_index], dense),
                        _qubit_ref(targets[pair_index + 1], dense),
                    ],
                    args=args,
                )
        elif name in {"DEPOLARIZE1", "DEPOLARIZE2"}:
            for target_index, target in enumerate(targets):
                append(
                    kind="COHERENT_Z",
                    source_instruction=source_index,
                    source_gate=name,
                    source_target_ordinal=target_index,
                    qubits=[_qubit_ref(target, dense)],
                    args=args,
                )
        elif name == "TICK":
            if targets:
                raise ValueError("TICK unexpectedly has targets")
            append(
                kind="TICK_MARKER",
                source_instruction=source_index,
                source_gate=name,
                args=args,
            )
        elif name in {"DETECTOR", "OBSERVABLE_INCLUDE"}:
            rec_operands: list[dict[str, int]] = []
            for operand_index, target in enumerate(targets):
                if not target.is_measurement_record_target:
                    raise ValueError(f"{name} has a non-rec target")
                negative_offset = int(target.value)
                absolute = raw_count + negative_offset
                if negative_offset >= 0 or not 0 <= absolute < raw_count:
                    raise ValueError(f"{name} has an invalid rec offset")
                rec_operands.append(
                    {
                        "negative_offset": negative_offset,
                        "absolute_raw_ordinal": absolute,
                        "operand_ordinal": operand_index,
                    }
                )
            if name == "DETECTOR":
                record_output = {"kind": "DETECTOR", "ordinal": detector_count}
                event = append(
                    kind="DETECTOR_APPEND",
                    source_instruction=source_index,
                    source_gate=name,
                    args=args,
                    rec_operands=rec_operands,
                    record_output=record_output,
                )
                outputs.append(
                    {
                        **record_output,
                        "producer_event_id": event["event_id"],
                    }
                )
                detector_count += 1
            else:
                if len(args) != 1 or int(args[0]) != 0:
                    raise ValueError("only observable zero is supported")
                observable_indices.append(0)
                append(
                    kind="OBSERVABLE_XOR",
                    source_instruction=source_index,
                    source_gate=name,
                    args=args,
                    rec_operands=rec_operands,
                )
        else:
            raise ValueError(f"unsupported canonical neutral operation: {name}")

    final = append(
        kind="FINALIZE_RECORD",
        source_instruction=None,
        source_gate="GENERATED",
        record_output={"kind": "OBSERVABLE", "ordinal": 0},
    )
    outputs.append(
        {
            "kind": "OBSERVABLE",
            "ordinal": 0,
            "producer_event_id": final["event_id"],
        }
    )
    if observable_indices != [0]:
        raise ValueError("frozen fixture must contain one observable-zero declaration")

    semantic = {
        "cell": {"distance": distance, "rounds": rounds},
        "fixture": {
            "manifest_path": str(FIXTURE_PATH.relative_to(REPO)),
            "manifest_sha256": FIXTURE_SHA256,
            "manifest_schema": FIXTURE_SCHEMA,
            "cell_identity": frozen_cell,
        },
        "source": {
            "stim_version": "1.16.0",
            "generator": "surface_code:rotated_memory_z",
            "generator_parameters": dict(manifest["generator_parameters"]),
            "source_text": source_text,
            "source_text_sha256": _sha256(source_text.encode("utf-8")),
        },
        "site_map": list(bundle["site_map"]),
        "process": {
            "name": "persistent_coherent_declared_error",
            "t": [1, 100],
            "c": [9999, 10001],
            "s": [200, 10001],
            "axis": "Z",
            "latent": {
                "name": "m",
                "domain": [-1, 1],
                "codec": [
                    {"bit": 0, "value": -1},
                    {"bit": 1, "value": 1},
                ],
                "prior": [[1, 2], [1, 2]],
                "transition": "identity_across_coherent_occurrences",
            },
        },
        "qubits": qubits,
        "events": events,
        "record_schema": {
            "raw_measurement_count": raw_count,
            "detector_count": detector_count,
            "observable_indices": [0],
            "outputs": outputs,
            "record_width": detector_count + 1,
        },
    }
    return StaticArtifact(NEUTRAL_SCHEMA, semantic)


def validate_declared_error_record_program(data: object) -> StaticArtifact:
    """Strictly reload a neutral artifact and reproduce its frozen semantics."""

    if not isinstance(data, dict):
        raise TypeError("neutral artifact must be a JSON object")
    _reject_forbidden_keys(data)
    reject_floats(data)
    if set(data) != {"_schema", "scope", "semantic", "semantic_sha256"}:
        raise ValueError("neutral artifact envelope has missing or unknown fields")
    if data["_schema"] != NEUTRAL_SCHEMA or data["scope"] != STATIC_SCOPE:
        raise ValueError("neutral artifact schema or scope mismatch")
    semantic = data["semantic"]
    if not isinstance(semantic, dict):
        raise TypeError("neutral semantic payload must be an object")
    if data["semantic_sha256"] != sha256_json(semantic):
        raise ValueError("neutral semantic hash mismatch")
    _validate_record_boundary_schema(semantic)
    cell = semantic.get("cell")
    if not isinstance(cell, dict) or set(cell) != {"distance", "rounds"}:
        raise ValueError("neutral cell schema mismatch")
    expected = lower_frozen_declared_error_record(
        distance=cell["distance"], rounds=cell["rounds"]
    )
    if canonical_json_bytes(data) != canonical_json_bytes(expected.to_data()):
        raise ValueError("neutral artifact does not reproduce frozen semantic identity")
    return expected
